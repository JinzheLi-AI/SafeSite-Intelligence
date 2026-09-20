import json
import pytest
import httpx
import openai
from types import SimpleNamespace
from unittest.mock import Mock
from sqlalchemy import select,create_engine,text
from app.core.config import Settings,settings
from app.ai.provider import create_safety_provider,get_provider
from app.ai.capabilities import readiness,workload,validate
from app.ai.deepseek import DeepSeekSafetyAIProvider
from app.ai.real import RealMultimodalSafetyAIProvider
from app.ai.mock import MockSafetyAIProvider
from app.ai.errors import AIProviderError
from app.ai.accounting import estimate,ensure_usage_columns
from app.models.entities import AIExecution
from app.main import app
from app.analyst.service import SafetyAnalystService
from test_real_provider import saved_image,observation,hazard,mitigation,analyze,context,provider as openai_provider
from test_analyst import population,NOW,planned

P='/api/v1'

def sdk(*outputs,usage=None):
    client=Mock();queue=list(outputs)
    def create(**kwargs):
        value=queue.pop(0) if len(queue)>1 else queue[0]
        if isinstance(value,Exception):raise value
        return SimpleNamespace(id='fixture-response',model=kwargs['model'],usage=usage,
            choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content=json.dumps(value)))])
    client.chat.completions.create.side_effect=create
    return client

def deepseek(*outputs,usage=None):
    config=Settings(_env_file=None,vision_provider='deepseek',vision_model='deepseek-flash')
    return DeepSeekSafetyAIProvider(config,sdk(*outputs,usage=usage))

@pytest.mark.parametrize('name,kind',[('openai',RealMultimodalSafetyAIProvider),('deepseek',DeepSeekSafetyAIProvider),('mock',MockSafetyAIProvider)])
def test_factory_selection(name,kind):
    config=Settings(_env_file=None,vision_provider=name,vision_model='deepseek-flash' if name=='deepseek' else 'gpt-5.6-terra')
    assert isinstance(create_safety_provider(config),kind)

def test_workloads_and_credentials_are_independent():
    config=Settings(_env_file=None,vision_provider='openai',vision_model='gpt-5.6-terra',openai_api_key='fixture',
        analyst_provider='deepseek',analyst_model='deepseek-v4-pro',deepseek_api_key=None,
        reinspection_provider='mock')
    assert readiness(config,'vision')['ready'] and readiness(config,'reinspection')['ready']
    assert not readiness(config,'analyst')['ready']
    config.deepseek_api_key='ignored'
    assert workload(config,'analyst')==('deepseek','deepseek-v4-pro')

@pytest.mark.parametrize('name,key_name',[('openai','OPENAI_API_KEY'),('deepseek','DEEPSEEK_API_KEY')])
def test_missing_keys(name,key_name,saved_image):
    config=Settings(_env_file=None,vision_provider=name,vision_model='deepseek-flash' if name=='deepseek' else 'gpt-5.6-terra',openai_api_key=None,deepseek_api_key=None)
    with pytest.raises(AIProviderError,match=key_name):analyze(create_safety_provider(config),saved_image)

@pytest.mark.parametrize('model',['deepseek-v4-pro','nonexistent'])
def test_unsupported_image_model_fails_before_call(model,saved_image):
    client=sdk(observation());config=Settings(_env_file=None,vision_provider='deepseek',vision_model=model)
    with pytest.raises(AIProviderError):analyze(create_safety_provider(config,client=client),saved_image)
    client.chat.completions.create.assert_not_called()

@pytest.mark.parametrize('count',[0,1,3])
def test_deepseek_normalization_matches_openai(count,saved_image):
    raw=observation([hazard() for _ in range(count)])
    a=analyze(openai_provider(raw),saved_image);b=analyze(deepseek(raw),saved_image)
    assert a.model_dump()==b.model_dump()
    if count:assert all(h.risk_score==85 for h in b.hazards) and b.requires_human_review

def test_actual_bytes_and_language_transported(saved_image):
    instance=deepseek(observation());instance.output_language='zh-CN';analyze(instance,saved_image)
    kw=instance._injected_client.chat.completions.create.call_args.kwargs
    assert kw['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
    assert 'zh-CN' in kw['messages'][0]['content'] and kw['response_format']=={'type':'json_object'}
    assert kw['extra_body']=={'thinking':{'type':'disabled'}}

def test_retry_accounts_for_each_request(saved_image):
    usage=SimpleNamespace(prompt_tokens=100,completion_tokens=20,total_tokens=120,prompt_cache_hit_tokens=0)
    instance=deepseek({'malformed':'object'},observation(),usage=usage)
    analyze(instance,saved_image)
    assert len(instance.call_records)==2
    assert [x['status'] for x in instance.call_records]==['FAILED','SUCCEEDED']
    assert all(x['input_tokens']==100 and x['latency_ms']>=0 for x in instance.call_records)

@pytest.mark.parametrize('usage',[None,SimpleNamespace(prompt_tokens=123,completion_tokens=45,total_tokens=168)])
def test_usage_persisted_in_existing_ledger(client,saved_image,db_factory,usage):
    instance=deepseek(observation(),usage=usage);app.dependency_overrides[get_provider]=lambda:instance
    ident=client.post(P+'/inspections',json={'project_id':1,'site_id':1,'location_text':'Fixture','source_type':'IMAGE','image_path':saved_image}).json()['id']
    assert client.post(f'{P}/inspections/{ident}/analyze').status_code==200
    with db_factory() as db:
        row=db.scalar(select(AIExecution))
        assert row.model_provider=='deepseek' and row.model_name=='deepseek-flash'
        assert row.input_tokens==(123 if usage else None) and row.output_tokens==(45 if usage else None)
        assert row.total_tokens==(168 if usage else None) and row.estimated_cost_usd is None
        assert row.call_records[0]['latency_ms']>=0 and row.latency_ms>=0

@pytest.mark.parametrize('error,code',[(openai.AuthenticationError,'invalid_credentials'),(openai.RateLimitError,'rate_limited'),(openai.NotFoundError,'model_unavailable'),(openai.BadRequestError,'invalid_provider_request'),(openai.InternalServerError,'provider_unavailable')])
def test_errors_sanitized_no_fallback(error,code,saved_image):
    secret='fake-sensitive-key'
    response=httpx.Response(500,request=httpx.Request('POST','https://api.deepseek.com/chat/completions'))
    instance=deepseek(error(secret,response=response,body={'key':secret}))
    with pytest.raises(AIProviderError) as caught:analyze(instance,saved_image)
    assert caught.value.code==code and secret not in str(caught.value)
    assert instance._injected_client.chat.completions.create.call_count==1
    assert secret not in json.dumps(instance.call_records)

def test_timeout_normalized(saved_image):
    instance=deepseek(openai.APITimeoutError(request=httpx.Request('POST','https://api.deepseek.com/chat/completions')))
    with pytest.raises(AIProviderError) as caught:analyze(instance,saved_image)
    assert caught.value.code=='timeout'

def test_deepseek_reinspection_same_conservative_output(saved_image):
    instance=deepseek(mitigation())
    result=instance.analyze_reinspection(incident_id=1,previous_risk=85,evidence_path=saved_image,notes='',original_hazard=context(saved_image))
    assert result.recommendation=='ELIGIBLE_FOR_CLOSURE' and result.current_risk_score==1
    assert instance.call_records[0]['workflow_name']=='reinspection-analysis'

def price(**kw):
    return dict(provider='fixture',model='fixture',input_price_per_million=2,output_price_per_million=10,
        cached_input_price_per_million=.2,effective_date='2026-01-01',valid_until='2026-12-31',
        source_note='Synthetic unit-test rates, never production prices',source_url='https://example.invalid',billing_mode='standard_token',image_tokens_in_usage=True,**kw)

def test_cost_math_with_cache_and_no_fabricated_usage():
    usage={'input_tokens':1000,'output_tokens':200,'cached_input_tokens':100}
    value,meta=estimate('fixture','fixture',usage,registry=[price()],now=NOW)
    assert value==pytest.approx(.00382) and meta['effective_date']=='2026-01-01'
    assert estimate('fixture','fixture',{'input_tokens':None,'output_tokens':20},registry=[price()],now=NOW)==(None,None)

@pytest.mark.parametrize('change',[{'provider':'unknown'},{'effective_date':'2027-01-01'},{'valid_until':'2025-01-01'},{'input_price_per_million':-1},{'source_note':''},{'billing_mode':'tiered'}])
def test_unreliable_or_missing_prices_null(change):
    assert estimate('fixture','fixture',{'input_tokens':100,'output_tokens':10,'cached_input_tokens':0},registry=[price()|change],now=NOW)==(None,None)

def test_image_pricing_unknown_null():
    assert estimate('fixture','fixture',{'input_tokens':100,'output_tokens':10,'cached_input_tokens':0},has_images=True,registry=[price()|{'image_tokens_in_usage':False}],now=NOW)==(None,None)

def test_usage_migration_idempotent_preserves_rows(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'old.db'))
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE ai_executions (id INTEGER PRIMARY KEY, model_name TEXT)'))
        conn.execute(text("INSERT INTO ai_executions VALUES (1,'old-model')"))
    ensure_usage_columns(engine);ensure_usage_columns(engine)
    with engine.connect() as conn:
        row=conn.execute(text('SELECT model_name,input_tokens,call_records FROM ai_executions')).one()
        assert tuple(row)==('old-model',None,None)
    engine.dispose()

def test_deepseek_analyst_sql_and_accounting(population,monkeypatch,db_factory):
    from app.analyst import provider
    from app.analyst.adapters import AnalystProvider
    monkeypatch.setattr(settings,'analyst_provider','deepseek');monkeypatch.setattr(settings,'analyst_model','deepseek-v4-pro')
    mock=sdk(planned(NOW).model_dump(),usage=SimpleNamespace(prompt_tokens=200,completion_tokens=80,total_tokens=280))
    monkeypatch.setattr(provider,'get_analyst_provider',lambda config,client=None:AnalystProvider(config,mock))
    result=SafetyAnalystService(population,now=NOW).ask('Break down incident totals per site for safety review')
    assert result.status=='success' and result.provider=='deepseek' and result.validation=='passed; metric results verified'
    with db_factory() as db:assert db.scalar(select(AIExecution)).total_tokens==280

def test_deepseek_sql_attack_still_rejected(population,monkeypatch):
    from app.analyst import provider
    from app.analyst.adapters import AnalystProvider
    monkeypatch.setattr(settings,'analyst_provider','deepseek');monkeypatch.setattr(settings,'analyst_model','deepseek-v4-pro')
    raw=planned(NOW).model_dump();raw['sql']='DELETE FROM safety_incidents'
    monkeypatch.setattr(provider,'get_analyst_provider',lambda config,client=None:AnalystProvider(config,sdk(raw)))
    assert SafetyAnalystService(population,now=NOW).ask('Break down incident totals per site for safety review').status=='rejected'


def test_independent_deepseek_reinspection_requires_human_closure(client,saved_image,db_factory,monkeypatch):
    from app.ai.provider import get_reinspection_provider
    from test_real_provider import create_real
    path=create_real(client,saved_image,openai_provider(observation()))
    assert client.post(path+'/analyze').status_code==200
    incident=client.post(path+'/confirm',json={}).json()[0]
    path=P+'/incidents/'+str(incident['id'])
    app.dependency_overrides[get_reinspection_provider]=lambda:deepseek(mitigation())
    assert client.post(path+'/start-rectification',json={}).status_code==200
    for action in incident['corrective_actions']:
        assert client.patch(path+'/actions/'+str(action['id']),json={'status':'COMPLETED'}).status_code==200
    response=client.post(path+'/reinspect',json={'evidence_path':saved_image})
    assert response.status_code==200
    result=response.json()
    assert result['status']=='REINSPECTION' and result['closed_at'] is None
    assert result['reinspection_source']['provider']=='deepseek'
    assert client.post(path+'/close',json={}).json()['status']=='CLOSED'


def test_official_deepseek_sdk_wire_format_offline(saved_image):
    def respond(request):
        body=json.loads(request.content)
        assert str(request.url)=='https://api.deepseek.com/chat/completions'
        assert body['thinking']=={'type':'disabled'}
        assert body['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
        return httpx.Response(200,json=dict(id='fixture',object='chat.completion',created=1,model='deepseek-flash',
            choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content=json.dumps(observation())))],
            usage=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120)))
    with openai.OpenAI(api_key='fixture-only',base_url='https://api.deepseek.com',http_client=httpx.Client(transport=httpx.MockTransport(respond))) as sdk_client:
        instance=DeepSeekSafetyAIProvider(Settings(_env_file=None,vision_model='deepseek-flash'),sdk_client)
        analyze(instance,saved_image)
        assert instance.call_records[0]['total_tokens']==120


def test_openai_usage_accounted_on_validation_retry(saved_image):
    instance=openai_provider(SimpleNamespace(status='completed',output=[],output_parsed=None,usage=None),observation())
    original=instance._injected_client.responses.parse.side_effect
    def parse(**kw):
        response=original(**kw)
        response.usage=SimpleNamespace(input_tokens=30,output_tokens=10,total_tokens=40,input_tokens_details=SimpleNamespace(cached_tokens=0))
        return response
    instance._injected_client.responses.parse.side_effect=parse
    analyze(instance,saved_image)
    assert len(instance.call_records)==2
    assert all(row['total_tokens']==40 for row in instance.call_records)


def test_readiness_and_ledger_never_return_credentials(client,monkeypatch):
    from pydantic import SecretStr
    monkeypatch.setattr(settings,'openai_api_key',SecretStr('fixture-openai-secret'))
    monkeypatch.setattr(settings,'deepseek_api_key',SecretStr('fixture-deepseek-secret'))
    for path in ['/health','/analyst/capabilities']:
        response=client.get(P+path)
        assert response.status_code==200
        assert 'fixture-openai-secret' not in response.text and 'fixture-deepseek-secret' not in response.text


def test_example_keys_empty_and_missing_pricing_null():
    from pathlib import Path
    text=Path('.env.example').read_text(encoding='utf-8-sig')
    for name in ['OPENAI_API_KEY','DEEPSEEK_API_KEY']:
        assert [line for line in text.splitlines() if line.startswith(name+'=')]==[name+'=']
    assert estimate('unpriced','unknown',{'input_tokens':1,'output_tokens':2},registry=[])==(None,None)
