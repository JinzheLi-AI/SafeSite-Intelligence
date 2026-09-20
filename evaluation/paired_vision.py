"""Paired production-provider evaluation. Default mode is completely offline."""
import argparse
import base64
import copy
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from evaluation.annotation_store import DatasetStore, atomic
from evaluation.label_vision_dataset import save_lock
from evaluation.vision_v2_scoring import score, eligibility, VERSION
VERSIONS=('vision-v1','vision-v2')
MODEL='gpt-5.6-sol'
DATASET=ROOT/'evaluation/datasets/vision_v2_development_v1.json'

def digest(data):return hashlib.sha256(data).hexdigest()
def fingerprint(value):return digest(json.dumps(value,sort_keys=True).encode())

def prepare(manifest=DATASET):
    from app.core.config import Settings
    from app.ai.prompts import VISION_SYSTEM_PROMPT
    from app.ai.vision_v2 import VISION_V2_SYSTEM_PROMPT
    from app.ai.images import image_data_url
    from app.core.config import settings
    manifest=Path(manifest).resolve()
    paths={'development':manifest,'historical':ROOT/'evaluation/datasets/vision_pilot_20.json','heldout':ROOT/'evaluation/datasets/vision_v2_heldout_v1.json'}
    validation=DatasetStore(ROOT/'evaluation',paths,save_lock).validate('development')
    if validation['errors'] or validation['benchmark_ready']!=10 or validation['total_cases']!=10:raise ValueError('Ten ready development cases required')
    raw=manifest.read_bytes();doc=json.loads(raw)
    if doc.get('split')!='development':raise ValueError('Development split only')
    config=Settings(_env_file=ROOT/'backend/.env').model_copy(update={'vision_provider':'openai','vision_model':MODEL})
    prompts={'vision-v1':VISION_SYSTEM_PROMPT,'vision-v2':VISION_V2_SYSTEM_PROMPT}
    processed={};old=settings.upload_dir
    try:
        for r in doc['cases']:
            path=ROOT/'evaluation'/r['image_path']
            if digest(path.read_bytes())!=r['image_hash']:raise ValueError('Image hash changed')
            settings.upload_dir=path.parent
            processed[r['case_id']]=digest(base64.b64decode(image_data_url('/uploads/'+path.name).split(',',1)[1]))
    finally:settings.upload_dir=old
    files=['real.py','images.py','prompts.py','vision_v2.py','vision_contracts.py','sanity.py','accounting.py']
    settings_public=dict(model=MODEL,provider='openai',timeout=config.ai_timeout_seconds,max_output_tokens=config.ai_max_output_tokens,
        validation_attempts=1,sdk_retries=0,detail='high',language='en',endpoint='https://api.openai.com/v1',
        implementation={f:digest((ROOT/'backend/app/ai'/f).read_bytes()) for f in files},
        normalization=digest((ROOT/'backend/app/schemas/contracts.py').read_bytes()),
        risk=digest((ROOT/'backend/app/services/risk.py').read_bytes()),
        scorer=digest((ROOT/'evaluation/vision_v2_scoring.py').read_bytes()),
        runner=digest(Path(__file__).read_bytes()))
    contract=dict(manifest_sha256=digest(raw),manifest_snapshot=doc,scoring_schema_version=VERSION,provider='openai',model=MODEL,
        prompt_hashes={v:digest(p.encode()) for v,p in prompts.items()},processed_hashes=processed,settings=settings_public)
    return contract,config,prompts

class Invocation:
    def __init__(self,config,prompts,offline):self.config=config;self.prompts=prompts;self.offline=offline
    def __call__(self,row,version,expected_hash):
        from app.ai.real import RealMultimodalSafetyAIProvider
        from app.ai.vision_contracts import VisualInspectionOutput
        from app.core.config import settings
        config=self.config.model_copy(update={'vision_prompt_version':version})
        self.last_accounting=[];self.last_latency=None
        provider=RealMultimodalSafetyAIProvider(config=config);provider.validation_attempts=1
        provider.output_language='en';receipt={};calls=0
        client=None
        if not self.offline:
            client=provider._create_client()
            assert client.max_retries==0 and str(client.base_url)=='https://api.openai.com/v1/'
        def parse(**kw):
            nonlocal calls
            calls+=1
            if calls!=1:raise RuntimeError('Retries prohibited')
            actual=kw['input'][0]['content']
            if not actual.startswith(self.prompts[version]+'\nPreferred output language: English (en).'):raise RuntimeError('Wrong actual prompt')
            parts=[x for item in kw['input'] if isinstance(item['content'],list) for x in item['content'] if x['type']=='input_image']
            actual_hash=digest(base64.b64decode(parts[0]['image_url'].split(',',1)[1]))
            if len(parts)!=1 or actual_hash!=expected_hash or kw['model']!=MODEL:raise RuntimeError('Request identity mismatch')
            receipt.update(actual_prompt_version=version,actual_prompt_sha256=digest(actual.encode()),processed_sha256=actual_hash)
            if self.offline:
                parsed=VisualInspectionOutput(summary='Synthetic offline fixture; not a real image prediction.',hazards=[],overall_confidence=.95,requires_human_review=False,ambiguity_detected=False,reasoning_notes=[])
                response=SimpleNamespace(status='completed',output=[],output_parsed=parsed,usage=None,model=MODEL,id='offline-fixture')
            else:response=client.responses.parse(**kw)
            receipt['returned_model']=getattr(response,'model',None)
            usage=getattr(response,'usage',None)
            receipt['raw_usage']=usage.model_dump() if hasattr(usage,'model_dump') else None
            # Durable raw response is persisted by the callback before product normalization.
            receipt['raw_response']=response.output_parsed.model_dump(mode='json') if response.output_parsed else None
            self.on_response(copy.deepcopy(receipt))
            return response
        provider._injected_client=SimpleNamespace(responses=SimpleNamespace(parse=parse))
        old=settings.upload_dir;path=ROOT/'evaluation'/row['image_path'];settings.upload_dir=path.parent
        started=time.perf_counter()
        try:
            if digest(path.read_bytes())!=row['image_hash']:raise ValueError('Image changed before inference')
            result=provider.analyze_inspection(location='',description=None,image_path='/uploads/'+path.name)
            return dict(provider_success=True,predicted_hazards=sorted({h.hazard_type.value if hasattr(h.hazard_type,'value') else h.hazard_type for h in result.hazards}),
                analysis=result.model_dump(mode='json'),model_uncertainty_review=result.model_uncertainty_review if version=='vision-v2' else None,
                operational_human_confirmation=result.operational_human_confirmation,requires_human_review=result.requires_human_review,**receipt)
        finally:
            self.last_accounting=provider.call_records
            self.last_latency=round((time.perf_counter()-started)*1000)
            settings.upload_dir=old
            if client:client.close()

def reports(state,out):
    doc=state['contract']['manifest_snapshot'];records=state['records'];paired={}
    common=[r for r in doc['cases'] if all(records.get(v+':'+r['case_id'],{}).get('provider_success') for v in VERSIONS)]
    metrics={};costs={}
    for v in VERSIONS:
        preds=[]
        for r in doc['cases']:
            p=records.get(v+':'+r['case_id'],{'case_id':r['case_id'],'provider_success':False})
            paired.setdefault(r['case_id'],{})[v]=p
            preds.append(p)
        cache=dict(scoring_schema_version=VERSION,manifest_sha256=state['contract']['manifest_sha256'],manifest_snapshot=doc,predictions=preds,
                   run_id=state['run_id'],mode=state['mode'],prompt_version=v,configuration=state['contract']['settings'])
        atomic(out/(v+'_cache.json'),cache)
        subset={**doc,'cases':common};chosen=[records[v+':'+r['case_id']] for r in common]
        metrics[v]=score(subset,chosen)
        atomic(out/(v+'_metrics.json'),metrics[v])
        attempted=[p for k,p in records.items() if k.startswith(v+':')]
        costs[v]={'attempted':len(attempted),'successful':sum(bool(p.get('provider_success')) for p in attempted)}
        for field in ['input_tokens','output_tokens','total_tokens']:
            vals=[p.get(field) for p in attempted];costs[v][field]=sum(vals) if vals and all(x is not None for x in vals) else None
        vals=[p['latency_ms'] for p in attempted if p.get('latency_ms') is not None]
        costs[v]['average_latency_ms']=sum(vals)/len(vals) if vals else None
    def diff(a,b):return b-a if a is not None and b is not None else None
    a,b=(metrics[v] for v in VERSIONS)
    delta={k:diff(a['micro'][k],b['micro'][k]) for k in ['precision','recall','f1']}
    delta.update(macro_f1=diff(a['macro']['f1'],b['macro']['f1']),ppe_false_positives=diff(a['per_class']['missing_ppe']['fp'],b['per_class']['missing_ppe']['fp']),
        safe_scene_false_positive_rate=diff(a['safe_scene']['false_positive_rate'],b['safe_scene']['false_positive_rate']),exact_match=diff(a['full_exact_match']['accuracy'],b['full_exact_match']['accuracy']))
    comparable=all(metrics[v]['uncertainty_review']['status']=='available' for v in VERSIONS)
    delta['uncertainty_review_recall']=diff(a['uncertainty_review']['recall'],b['uncertainty_review']['recall']) if comparable else None
    atomic(out/'paired_report.json',dict(mode=state['mode'],paired_predictions=paired,common_successful_cases=[r['case_id'] for r in common],
        planned_cases=10,paired_coverage=len(common)/10,differences_v2_minus_v1=delta,uncertainty_comparable=comparable,accounting=costs,
        limitation='10 development images, not independent held-out validation; no statistical significance claimed. Offline predictions are synthetic.' if state['mode']=='offline' else '10 development images, not independent held-out validation; no statistical significance claimed.'))
    (out/'summary.md').write_text('# Paired Vision evaluation\n\nMode: '+state['mode']+'\n\nCommon successful cases: '+str(len(common))+'/10. Both metric files use exactly this intersection. Full caches retain failures/unattempted cases.\n\nSee paired_report.json for predictions, differences and accounting; vision-v1_metrics.json and vision-v2_metrics.json include masked error analysis. Undefined/incomparable differences are null.\n\nTen development images are not independent held-out validation; no statistical significance claimed. Offline results are synthetic, never accuracy evidence.\n',encoding='utf-8')

def run(out,offline=True,resume=False,report_only=False,invoke=None):
    contract,config,prompts=prepare();out=Path(out);mode='offline' if offline else 'live'
    print(json.dumps(dict(planned_paid_requests=0 if offline else 20,maximum_inference_attempts=20,model=MODEL,prompt_versions=VERSIONS,dataset=str(DATASET),output=str(out))))
    if not resume:
        out.mkdir(parents=True,exist_ok=False)
    with save_lock(out/'paired-run'):
        path=out/'state.json'
        if resume:
            state=json.loads(path.read_text(encoding='utf-8'))
            if state['contract']!=contract or state['mode']!=mode:raise ValueError('Resume contract mismatch')
        else:
            state=dict(run_id=out.name,mode=mode,contract=contract,records={},consecutive_network_failures=0,stopped=False);atomic(path,state)
        expected={v+':'+r['case_id']:(v,r) for r in contract['manifest_snapshot']['cases'] for v in VERSIONS}
        for key,entry in state['records'].items():
            if key not in expected:raise ValueError('Unknown cached case/prompt')
            v,r=expected[key]
            checks=dict(case_id=r['case_id'],image_hash=r['image_hash'],provider='openai',requested_model=MODEL,prompt_version=v,
                        configuration_fingerprint=fingerprint(contract),prompt_sha256=contract['prompt_hashes'][v])
            if any(entry.get(k)!=value for k,value in checks.items()):raise ValueError('Cached record identity mismatch')
            if entry.get('provider_success') and (entry.get('actual_prompt_version')!=v or entry.get('processed_sha256')!=contract['processed_hashes'][r['case_id']]):raise ValueError('Cached request provenance mismatch')
        if not report_only and not state['stopped']:
            if not offline and not config.openai_api_key:raise ValueError('OpenAI credential unavailable')
            invoke=invoke or Invocation(config,prompts,offline)
            for row in contract['manifest_snapshot']['cases']:
                for v in VERSIONS:
                    key=v+':'+row['case_id']
                    if key in state['records']:continue # Includes uncertain/in-flight attempts: never recharge.
                    if len(state['records'])>=20:raise RuntimeError('Attempt budget exceeded')
                    entry=dict(case_id=row['case_id'],image_hash=row['image_hash'],provider='openai',requested_model=MODEL,prompt_version=v,
                        configuration_fingerprint=fingerprint(contract),prompt_sha256=contract['prompt_hashes'][v],provider_success=False,status='attempt_reserved',provider_error='interrupted_or_unresolved')
                    state['records'][key]=entry;atomic(path,state) # Durable write BEFORE possibly billed request.
                    def on_response(receipt):
                        entry.update(receipt);atomic(path,state)
                    invoke.on_response=on_response
                    try:
                        entry.update(invoke(row,v,contract['processed_hashes'][row['case_id']]))
                        entry.update(status='completed',provider_error=None)
                        state['consecutive_network_failures']=0
                    except Exception as exc:
                        code=getattr(exc,'code','local_execution_error')
                        entry.update(status='failed',provider_error=code)
                        state['consecutive_network_failures']=state['consecutive_network_failures']+1 if code in ['connection_error','timeout'] else 0
                    entry['latency_ms']=getattr(invoke,'last_latency',None)
                    entry['call_records']=getattr(invoke,'last_accounting',[])
                    for f in ['input_tokens','output_tokens','total_tokens']:
                        vals=[a.get(f) for a in entry['call_records']];entry[f]=sum(vals) if vals and all(x is not None for x in vals) else None
                    if state['consecutive_network_failures']>=2 or entry['provider_error'] in {'local_execution_error','invalid_credentials','rate_limited','model_unavailable','invalid_output','invalid_provider_request','missing_credentials'}:state['stopped']=True
                    atomic(path,state)
                    if state['stopped']:break
                if state['stopped']:break
        reports(state,out)
    return state

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-live',action='store_true');p.add_argument('--network-enabled',action='store_true',help='Explicit acknowledgement of approved network-enabled host')
    p.add_argument('--output',type=Path);p.add_argument('--resume',action='store_true');p.add_argument('--report-only',action='store_true');a=p.parse_args()
    if a.execute_live and not a.network_enabled and not a.report_only:p.error('Live execution requires --network-enabled in the approved network-enabled environment')
    if (a.resume or a.report_only) and not a.output:p.error('Existing --output is required')
    out=a.output or ROOT/'evaluation/reports'/('paired_'+('live_' if a.execute_live else 'offline_')+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8])
    run(out,offline=not a.execute_live,resume=a.resume or a.report_only,report_only=a.report_only)
if __name__=='__main__':main()
