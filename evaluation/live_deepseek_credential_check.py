"""Single-request DeepSeek credential revalidation using only the safe fixture. Never imports workflows."""
import argparse
import base64
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
os.chdir(ROOT/'backend')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not args.execute:parser.error('Explicit --execute is required; this can incur API charges.')
    logging.basicConfig(level=logging.WARNING)
    for name in ['openai','httpx','httpcore']:logging.getLogger(name).setLevel(logging.CRITICAL)
    from app.core.config import settings
    from app.ai.provider import create_safety_provider
    from app.ai.deepseek import DeepSeekSafetyAIProvider
    from app.ai.images import image_data_url
    from app.ai.errors import AIProviderError
    from app.ai.accounting import attach
    from app.models.entities import AIExecution
    from app.schemas.contracts import HazardType,InspectionAnalysis
    from app.services.risk import RiskEngine
    from PIL import Image

    assert settings.deepseek_api_key and settings.deepseek_api_key.get_secret_value().strip()
    # User explicitly requested Flash; .env still selects OpenAI. Process-local only.
    config=settings.model_copy(update={'vision_provider':'deepseek','vision_model':'deepseek-flash'})
    from dotenv import dotenv_values
    assert settings.deepseek_api_key.get_secret_value()==dotenv_values('.env').get('DEEPSEEK_API_KEY')
    product_before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend/app').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    env_hash=hashlib.sha256(Path('.env').read_bytes()).digest()
    fixture_root=ROOT/'evaluation/fixtures/live_smoke'
    output=ROOT/'evaluation/reports/deepseek_credential_revalidation'
    output.mkdir(parents=True,exist_ok=True)
    # Durable one-shot guard: never rerun a possibly paid request after interruption.
    with (output/'execution.lock').open('x',encoding='utf-8') as f:
        f.write(datetime.now(timezone.utc).isoformat())
    result={'started_at':datetime.now(timezone.utc).isoformat(),'provider':'deepseek','model':'deepseek-flash',
        'maximum_requests':1,'sdk_retries':0,'validation_attempts':1,'requests_attempted':0,
        'incident_operations':0,'cases':[]}
    def save():
        (output/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    save()
    old_root=settings.upload_dir
    settings.upload_dir=fixture_root
    try:
        for name in ['01_safe.jpg']:
            path=fixture_root/name
            original=path.read_bytes()
            row={'image':name,'sha256':hashlib.sha256(original).hexdigest(),'bytes':len(original),
                'provider':'deepseek','model':'deepseek-flash','requests_attempted':0,'status':'preflight',
                'input_tokens':None,'output_tokens':None,'total_tokens':None,'estimated_cost_usd':None,
                'latency_ms':None,'error':None,'call_records':[]}
            result['cases'].append(row);save()
            with Image.open(path) as im:
                row.update(width=im.width,height=im.height,format=im.format);im.verify()
            provider=create_safety_provider(config)
            assert type(provider) is DeepSeekSafetyAIProvider
            provider.validation_attempts=1
            row['prompt_version']=provider.prompt_version
            try:
                data_url=image_data_url('/uploads/'+name)
                processed=base64.b64decode(data_url.split(',',1)[1])
                from io import BytesIO
                with Image.open(BytesIO(processed)) as im:row['processed_dimensions']=list(im.size)
                row['processed_sha256']=hashlib.sha256(processed).hexdigest()
                row['processed_bytes']=len(processed)
                prior_dir='live_openai_safe_preprocessed' if name=='01_safe.jpg' else 'live_openai_smoke'
                prior=json.loads((ROOT/'evaluation/reports'/prior_dir/'results.json').read_text())
                prior_case=next(c for c in prior['cases'] if c['image']==name and c['status']=='succeeded')
                assert row['processed_sha256']==prior_case.get('processed_sha256',prior_case['sha256'])
                row['identical_bytes_to_saved_openai_case']=True
            except AIProviderError as exc:
                row.update(status='blocked_preflight',error={'code':exc.code,'message':exc.message})
                save();continue
            client=provider._create_client()
            assert client.max_retries==0 and str(client.base_url).rstrip('/')=='https://api.deepseek.com'
            def check_request(request):
                assert request.method=='POST' and str(request.url)=='https://api.deepseek.com/chat/completions'
                assert result['requests_attempted']<result['maximum_requests'] and row['requests_attempted']==0
                body=json.loads(request.content)
                assert body['model']=='deepseek-flash' and body['stream'] is False
                assert body['response_format']=={'type':'json_object'} and body['thinking']=={'type':'disabled'}
                parts=[p for item in body['messages'] if isinstance(item.get('content'),list) for p in item['content'] if p.get('type')=='image_url']
                assert len(parts)==1 and base64.b64decode(parts[0]['image_url']['url'].split(',',1)[1])==processed
                assert name not in json.dumps(body)
                row['image_bytes_verified_in_request']=True
                result['requests_attempted']+=1;row['requests_attempted']+=1;save()
            def check_response(response):
                row['http_status']=response.status_code
                save()
            client._client.event_hooks['request']=[check_request]
            client._client.event_hooks['response']=[check_response]
            provider._injected_client=client
            started=time.perf_counter()
            try:
                analysis=provider.analyze_inspection(location='',description=None,image_path='/uploads/'+name)
                InspectionAnalysis.model_validate(analysis.model_dump())
                raw=provider.last_visual_output
                checks=[]
                for hazard in analysis.hazards:
                    assert hazard.hazard_type in [x.value for x in HazardType]
                    risk=RiskEngine.assess(hazard.hazard_type,hazard.severity,hazard.exposure,hazard.probability,hazard.confidence)
                    assert risk.final_score==hazard.risk_score and risk.risk_level==hazard.risk_level
                    checks.append(risk.model_dump(mode='json'))
                if analysis.hazards:assert analysis.requires_human_review
                row.update(status='succeeded',analysis=analysis.model_dump(mode='json'),
                    structured_output_valid=True,risk_engine_verified=True,risk_breakdowns=checks,
                    raw_observations=raw.model_dump(mode='json'),no_mock_fallback=True)
            except Exception as exc:
                # Never serialize provider bodies, headers, raw exceptions or credentials.
                row.update(status='failed',error={'code':getattr(exc,'code',type(exc).__name__),
                    'message':exc.message if isinstance(exc,AIProviderError) else 'Request or validation failed; raw exception omitted.'})
                cause=exc.__context__
                if cause is not None and isinstance(getattr(cause,'status_code',None),int):row['http_status']=cause.status_code
            finally:
                row['elapsed_ms']=round((time.perf_counter()-started)*1000)
                client.close()
                execution=AIExecution()
                attach(execution,provider,row.get('analysis',{}).get('overall_confidence'))
                row['call_records']=execution.call_records or []
                for field in ['input_tokens','output_tokens','total_tokens','estimated_cost_usd']:row[field]=getattr(execution,field)
                if row['call_records']:row['latency_ms']=row['call_records'][0]['latency_ms']
                assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
                save()
    finally:
        settings.upload_dir=old_root
        result['env_unchanged']=hashlib.sha256(Path('.env').read_bytes()).digest()==env_hash
        result['images_unchanged']=all(hashlib.sha256((fixture_root/r['image']).read_bytes()).hexdigest()==r['sha256'] for r in result['cases'])
        result['product_code_unchanged']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in product_before.items())
        result['completed_at']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Smoke runner stopped safely: '+type(exc).__name__+'. No automatic retry.');sys.exit(1)
