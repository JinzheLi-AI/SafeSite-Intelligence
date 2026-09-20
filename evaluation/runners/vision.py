"""Opt-in paired real calls. Placeholder manifests can never produce accuracy scores."""
import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from app.ai.deepseek import DeepSeekSafetyAIProvider
from app.ai.capabilities import validate, key_for, workload
from app.ai.real import RealMultimodalSafetyAIProvider
from app.ai.vision_contracts import VisualInspectionOutput
from app.ai.images import image_data_url
from app.ai.sanity import review_notes
from app.core.config import settings
from evaluation.schema import Prediction, VERIFIED, PENDING
from evaluation.metrics import hazards

GENERIC_PROMPT='Inspect the construction image and identify visible safety hazards in the supplied categories. Describe your observations and uncertainty using the supplied output schema.'

class RecordingProvider(RealMultimodalSafetyAIProvider):
    raw=None
    def _create_client(self):
        client=super()._create_client()
        self.receipts=[]
        def parse(**kwargs):
            response=client.responses.parse(**kwargs)
            usage=getattr(response,'usage',None)
            self.receipts.append({'response_id':getattr(response,'id',None),'returned_model':getattr(response,'model',None),
                'status':response.status,'usage':usage.model_dump() if usage else None,
                'system_prompt_sha256':hashlib.sha256(kwargs['input'][0]['content'].encode()).hexdigest()})
            return response
        return SimpleNamespace(close=client.close,responses=SimpleNamespace(parse=parse))
    def _request(self,prompt,content,schema):
        self.prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
        self.raw=super()._request(prompt,content,schema)
        return self.raw

class RecordingDeepSeekProvider(DeepSeekSafetyAIProvider):
    raw=None
    def _request(self,prompt,content,schema):
        self.prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
        self.raw=super()._request(prompt,content,schema)
        return self.raw

def run(cases,image_root,output,live=False,limit=100,model_id=None,validation_attempts=2):
    if validation_attempts not in (1,2):raise ValueError('Validation attempts must be 1 or 2')
    default_provider,_=workload(settings,'vision')
    provider_name,separator,model=(model_id or ('openai' if default_provider=='mock' else default_provider)+'/'+settings.vision_model).partition('/')
    if not separator or not model:raise ValueError('Model must use provider/model syntax')
    validate(provider_name,model,'vision')
    config=settings.model_copy(update={'vision_model':model})
    reviewed=[c for c in cases if c.label_status=='reviewed']
    result={'status':PENDING,'manifest_cases':len(cases),'reviewed_cases':len(reviewed),'baselines':{},
            'provider':provider_name,'model':model,'model_id':provider_name+'/'+model,
            'reason':'Requires reviewed real images, configured credentials and explicit --live-vision.'}
    if not live or not reviewed or not key_for(config,provider_name) or not key_for(config,provider_name).get_secret_value().strip():return result
    selected=reviewed[:limit]
    paths={}
    for case in selected:
        path=(image_root/case.image_path).resolve()
        if not path.is_relative_to(image_root.resolve()) or not path.is_file():raise ValueError('Image must exist within image-root')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=case.image_sha256.lower():raise ValueError('Image hash mismatch: '+case.case_id)
        paths[case.case_id]=path
    predictions={'generic_direct':[],'safesite':[]};records=[]
    old_root=settings.upload_dir
    with tempfile.TemporaryDirectory(prefix='safesite-eval-images-') as temp:
        try:
            settings.upload_dir=Path(temp)
            for i,case in enumerate(selected):
                source=paths[case.case_id];name='evaluation'+source.suffix.lower()
                shutil.copyfile(source,Path(temp)/name);image_path='/uploads/'+name
                # Alternate order, same image bytes/model/language/schema/token budget/retry policy.
                for baseline in (list(predictions) if i%2==0 else list(reversed(predictions))):
                    started=time.perf_counter();provider=(RecordingDeepSeekProvider(config=config) if provider_name=='deepseek' else RecordingProvider(config=config) if model_id else RecordingProvider());provider.output_language='en';provider.validation_attempts=validation_attempts
                    if baseline=='generic_direct':provider.prompt_version='evaluation-generic-v1'
                    row={'case_id':case.case_id,'baseline':baseline,'image_sha256':case.image_sha256,'provider':provider_name,'model':provider.model_name,'model_id':provider_name+'/'+model,'prompt_version':getattr(provider,'prompt_version',None),'error':None}
                    try:
                        if baseline=='generic_direct':
                            raw=provider._request(GENERIC_PROMPT,[{'type':'input_text','text':'Inspect this image.'},
                                {'type':'input_image','image_url':image_data_url(image_path),'detail':'high'}],VisualInspectionOutput)
                            p=Prediction(case_id=case.case_id,hazards=[h.hazard_type for h in raw.hazards],requires_human_review=raw.requires_human_review,
                                         uncertain=raw.ambiguity_detected or raw.overall_confidence<.85)
                        else:
                            answer=provider.analyze_inspection(location='',description=None,image_path=image_path)
                            raw=provider.raw
                            p=Prediction(case_id=case.case_id,hazards=[h.hazard_type for h in answer.hazards],requires_human_review=answer.requires_human_review,
                                uncertain=raw.ambiguity_detected or raw.overall_confidence<.85 or len(review_notes(raw))>len(raw.reasoning_notes))
                        row.update(raw_output=raw.model_dump(mode='json'),prompt_sha256=provider.prompt_hash)
                    except Exception as exc:
                        row['error']=getattr(exc,'code',type(exc).__name__)
                        p=Prediction(case_id=case.case_id,hazards=[],requires_human_review=False,error=row['error'])
                    predictions[baseline].append(p);row.update(prediction=p.model_dump(),latency_ms=round((time.perf_counter()-started)*1000));row['api_receipts']=getattr(provider,'receipts',[]);row['call_records']=getattr(provider,'call_records',[])
                    for field in ['input_tokens','output_tokens','total_tokens','estimated_cost_usd']:
                        values=[call.get(field) for call in row['call_records']]
                        row[field]=sum(values) if values and all(v is not None for v in values) else None
                    records.append(row)
                    (output/'vision-calls.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        finally:settings.upload_dir=old_root
    result.update(status=VERIFIED,reason=None,evaluated_cases=len(selected),model=model,
        max_output_tokens=settings.ai_max_output_tokens,language='en',max_validation_attempts=validation_attempts,
        basis='Paired live calls on reviewed images. Small sample; no superiority claim without held-out validation.',
        baselines={name:{'status':VERIFIED,'metrics':hazards(selected,values),'predictions':[p.model_dump() for p in values]} for name,values in predictions.items()})
    return result
