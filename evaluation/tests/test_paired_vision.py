import copy
import json
from pathlib import Path
import pytest
from evaluation.paired_vision import run, ROOT

def test_full_offline_resume_reports(tmp_path,monkeypatch):
    import socket
    monkeypatch.setattr(socket.socket,'connect',lambda *a: (_ for _ in ()).throw(AssertionError('Network prohibited')))
    out=tmp_path/'paired';state=run(out)
    assert len(state['records'])==20
    for version in ['vision-v1','vision-v2']:
        rows=[r for r in state['records'].values() if r['prompt_version']==version]
        assert len(rows)==10 and all(r['provider_success'] and r['actual_prompt_version']==version for r in rows)
        m=json.loads((out/(version+'_metrics.json')).read_text(encoding='utf-8'))
        assert m['scoring_schema_version']=='vision-three-state-v1'
        assert m['per_class']['housekeeping']['evaluable_sample_count']==9
        assert m['safe_scene']['confirmed_count']==3
        assert m['full_exact_match']['evaluable_count']==9
        if version=='vision-v1':assert m['uncertainty_review']['status']=='unavailable'
    for cid in state['contract']['processed_hashes']:
        a,b=[state['records'][v+':'+cid] for v in ['vision-v1','vision-v2']]
        assert a['actual_prompt_sha256']!=b['actual_prompt_sha256']
        assert a['processed_sha256']==b['processed_sha256']
    before=(out/'paired_report.json').read_bytes()
    def forbidden(*a):raise AssertionError('Duplicate invocation')
    assert run(out,resume=True,invoke=forbidden)['records']==state['records']
    run(out,resume=True,report_only=True,invoke=forbidden)
    assert (out/'paired_report.json').read_bytes()==before
    cache=json.loads((out/'state.json').read_text(encoding='utf-8'));next(iter(cache['records'].values()))['image_hash']='wrong'
    (out/'state.json').write_text(json.dumps(cache),encoding='utf-8')
    with pytest.raises(ValueError,match='identity mismatch'):run(out,resume=True,invoke=forbidden)

def test_two_network_failures_stop_and_do_not_retry(tmp_path):
    from app.ai.errors import AIProviderError
    class Fail:
        calls=0
        def __call__(self,*a):
            self.calls+=1
            raise AIProviderError('connection_error','synthetic')
    f=Fail();out=tmp_path/'stopped';state=run(out,invoke=f)
    assert f.calls==2 and len(state['records'])==2 and state['stopped']
    run(out,resume=True,invoke=f);assert f.calls==2

def test_interruption_reservation_prevents_recharge(tmp_path):
    class Interrupt:
        def __call__(self,*a):raise KeyboardInterrupt()
    out=tmp_path/'interrupted'
    with pytest.raises(KeyboardInterrupt):run(out,invoke=Interrupt())
    state=run(out,resume=True)
    assert len(state['records'])==20
    first=next(iter(state['records'].values()))
    assert first['status']=='attempt_reserved' and not first['provider_success']
    report=json.loads((out/'paired_report.json').read_text(encoding='utf-8'))
    assert len(report['common_successful_cases'])==9


@pytest.mark.parametrize('code',['invalid_credentials','rate_limited','model_unavailable','invalid_output','invalid_provider_request'])
def test_fatal_provider_failure_stops_immediately(tmp_path,code):
    from app.ai.errors import AIProviderError
    class Fail:
        calls=0
        def __call__(self,*a):
            self.calls+=1
            raise AIProviderError(code,'synthetic')
    f=Fail();state=run(tmp_path/code,invoke=f)
    assert f.calls==1 and state['stopped'] and len(state['records'])==1
