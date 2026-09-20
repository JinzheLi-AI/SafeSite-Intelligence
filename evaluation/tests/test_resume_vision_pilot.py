from evaluation.resume_vision_pilot import already_attempted

def test_resume_never_recharges_success_failure_or_uncertain_attempt():
    for success,error in [(True,None),(False,'connection_error'),(False,'in_flight_outcome_unknown')]:
        assert already_attempted([dict(case_id='case_001',requests_attempted=1,provider_success=success,provider_error=error)],'case_001')

def test_resume_allows_only_unattempted_cases():
    assert not already_attempted([dict(case_id='case_001',requests_attempted=0)],'case_001')
    assert not already_attempted([dict(case_id='case_001',requests_attempted=1)],'case_002')

import base64
import hashlib
import json
from io import BytesIO
from types import SimpleNamespace
import pytest
from PIL import Image
from evaluation import resume_vision_pilot as runner

@pytest.fixture
def offline_runner(tmp_path,monkeypatch):
    from app.core.config import settings
    from app.ai.errors import AIProviderError
    from pydantic import SecretStr
    import app.ai.real
    import app.ai.images
    import evaluation.validate_vision_dataset
    (tmp_path/'backend/app/ai').mkdir(parents=True)
    (tmp_path/'backend/app/ai/prompts.py').write_text('frozen test prompt')
    (tmp_path/'backend/.env').write_text('')
    (tmp_path/'evaluation').mkdir()
    buffer=BytesIO();Image.new('RGB',(2,2)).save(buffer,format='PNG');data=buffer.getvalue()
    manifest=tmp_path/'evaluation/manifest.json'
    cases=[]
    for n in range(1,21):
        name=f'{n}.png';(tmp_path/'evaluation'/name).write_bytes(data)
        cases.append(dict(case_id=f'case_{n:03d}',image_path=name,image_hash=hashlib.sha256(data).hexdigest()))
    manifest.write_text(json.dumps(cases))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner,'MANIFEST',manifest);monkeypatch.setattr(runner,'OUTPUT',tmp_path/'out')
    monkeypatch.setattr(settings,'vision_provider','openai');monkeypatch.setattr(settings,'vision_model','gpt-5.6-sol');monkeypatch.setattr(settings,'openai_api_key',SecretStr('test-placeholder'))
    monkeypatch.setattr(evaluation.validate_vision_dataset,'validate_dataset',lambda _:dict(errors=[],benchmark_ready=20))
    url='data:image/png;base64,'+base64.b64encode(data).decode()
    monkeypatch.setattr(app.ai.images,'image_data_url',lambda _:url)
    control=dict(attempts=0,fail_at=set())
    class Fake:
        def __init__(self):self.call_records=[]
        def _create_client(self):
            return SimpleNamespace(max_retries=0,_client=SimpleNamespace(event_hooks={}),close=lambda:None)
        def analyze_inspection(self,**kwargs):
            request=SimpleNamespace(method='POST',url='https://api.openai.com/v1/responses',content=json.dumps(dict(model='gpt-5.6-sol',input=[dict(content='unchanged'),dict(content=[dict(type='input_image',image_url=url)])])).encode())
            self._injected_client._client.event_hooks['request'][0](request)
            control['attempts']+=1
            if control['attempts'] in control['fail_at']:raise AIProviderError('connection_error','synthetic offline failure')
            raw=dict(hazards=[],requires_human_review=False)
            self.last_visual_output=SimpleNamespace(model_dump=lambda **_:raw)
            self.call_records=[dict(input_tokens=1,output_tokens=1,total_tokens=2,latency_ms=1,returned_model='gpt-5.6-sol')]
            return SimpleNamespace(model_dump=lambda **_:raw,overall_confidence=.95,requires_human_review=False)
    monkeypatch.setattr(app.ai.real,'RealMultimodalSafetyAIProvider',Fake)
    return control

def test_checkpoint_then_resume_exactly_twenty_without_repeat(offline_runner):
    r=runner.execute(checkpoint=True)
    assert r['requests_attempted']==1 and r['cases'][0]['provider_success']
    r=runner.execute()
    assert r['requests_attempted']==20 and offline_runner['attempts']==20
    runner.execute()
    assert offline_runner['attempts']==20

def test_failed_checkpoint_stops_after_one(offline_runner):
    offline_runner['fail_at']={1}
    r=runner.execute(checkpoint=True)
    assert r['requests_attempted']==1 and r['stop_reason'].startswith('checkpoint_failed')
    with pytest.raises(AssertionError):runner.execute()
    assert offline_runner['attempts']==1

def test_two_consecutive_network_failures_stop(offline_runner):
    runner.execute(checkpoint=True)
    offline_runner['fail_at']={2,3}
    r=runner.execute()
    assert r['requests_attempted']==3 and r['stop_reason']=='two_consecutive_network_failures'
