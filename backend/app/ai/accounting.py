"""Nullable per-attempt accounting; never store prompts, images, secrets or raw errors."""
import json
import time
from datetime import datetime,timezone,date
from decimal import Decimal,InvalidOperation
from sqlalchemy import inspect,text
from app.core.config import settings

FIELDS={'input_tokens':'INTEGER','output_tokens':'INTEGER','total_tokens':'INTEGER','estimated_cost_usd':'FLOAT','call_records':'JSON'}
def ensure_usage_columns(engine):
    if engine.dialect.name=='sqlite' and 'ai_executions' in inspect(engine).get_table_names():
        with engine.begin() as conn:
            present={x['name'] for x in inspect(conn).get_columns('ai_executions')}
            for name,sql_type in FIELDS.items():
                if name not in present:conn.execute(text(f'ALTER TABLE ai_executions ADD COLUMN {name} {sql_type}'))

def integer(value):return value if type(value) is int and value>=0 else None

def read(obj,name):
    return obj.get(name) if isinstance(obj,dict) else getattr(obj,name,None) if obj is not None else None

def estimate(provider,model,usage,*,has_images=False,registry=None,now=None):
    now=now or datetime.now(timezone.utc)
    try:
        entries=registry if registry is not None else json.loads(settings.pricing_file.read_text(encoding='utf-8-sig'))
        matching=[e for e in entries if e['provider']==provider and e['model']==model
                  and date.fromisoformat(e['effective_date'])<=now.date()<=date.fromisoformat(e['valid_until'])]
        if len(matching)!=1:return None,None
        e=matching[0]
        if not e.get('source_note') or not e.get('source_url') or e.get('billing_mode')!='standard_token':return None,None
        if has_images and not e.get('image_tokens_in_usage'):return None,None
        inp,out=usage.get('input_tokens'),usage.get('output_tokens')
        if inp is None or out is None or (e.get('max_input_tokens') is not None and inp>e['max_input_tokens']):return None,None
        if usage.get('cache_write_tokens') not in (None,0):return None,None
        cached=usage.get('cached_input_tokens')
        if not e.get('uniform_input_rate') and cached is None:return None,None
        cached=cached or 0
        if cached>inp:return None,None
        ir=Decimal(str(e['input_price_per_million']));orr=Decimal(str(e['output_price_per_million']))
        cr=ir if e.get('uniform_input_rate') else Decimal(str(e['cached_input_price_per_million']))
        if any(not r.is_finite() or r<0 for r in (ir,orr,cr)):return None,None
        cost=(Decimal(inp-cached)*ir+Decimal(cached)*cr+Decimal(out)*orr)/Decimal(1000000)
        return float(cost),{k:e[k] for k in list(e)}
    except (OSError,ValueError,KeyError,TypeError,InvalidOperation):return None,None

def begin(owner,workflow,prompt_version):
    if not hasattr(owner,'call_records'):owner.call_records=[]
    row=dict(workflow_name=workflow,provider=owner.model_provider,model_name=owner.model_name,prompt_version=prompt_version,
             status='FAILED',confidence=None,input_tokens=None,output_tokens=None,total_tokens=None,
             estimated_cost_usd=None,error_message=None,started_at=datetime.now(timezone.utc).isoformat())
    owner.call_records.append(row)
    return row,time.perf_counter()

def capture(row,response,*,has_images=False):
    usage=read(response,'usage')
    names=('prompt_tokens','completion_tokens','total_tokens') if row['provider']=='deepseek' else ('input_tokens','output_tokens','total_tokens')
    for target,source in zip(['input_tokens','output_tokens','total_tokens'],names):row[target]=integer(read(usage,source))
    detail=read(usage,'prompt_tokens_details' if row['provider']=='deepseek' else 'input_tokens_details')
    row['cached_input_tokens']=integer(read(usage,'prompt_cache_hit_tokens')) if row['provider']=='deepseek' and integer(read(usage,'prompt_cache_hit_tokens')) is not None else integer(read(detail,'cached_tokens'))
    row['cache_write_tokens']=integer(read(detail,'cache_write_tokens'))
    row['estimated_cost_usd'],row['pricing']=estimate(row['provider'],row['model_name'],row,has_images=has_images)
    row['response_id']=read(response,'id') if isinstance(read(response,'id'),str) else None
    row['returned_model']=read(response,'model') if isinstance(read(response,'model'),str) else None

def finish(row,started):
    row['latency_ms']=max(0,round((time.perf_counter()-started)*1000))
    if row['status']!='SUCCEEDED' and not row['error_message']:row['error_message']='invalid_or_incomplete_output'

def attach(execution,owner,confidence=None):
    rows=getattr(owner,'call_records',[])
    owner.call_records=[]
    for row in rows:row['confidence']=confidence if row['status']=='SUCCEEDED' else None
    execution.call_records=rows or None
    for field in ['input_tokens','output_tokens','total_tokens','estimated_cost_usd']:
        values=[row[field] for row in rows]
        setattr(execution,field,sum(values) if values and all(v is not None for v in values) else None)

def normalize_error(exc):
    from app.ai.errors import AIProviderError
    if isinstance(exc,AIProviderError):return exc
    import openai
    rules=[(openai.AuthenticationError,'invalid_credentials',503),(openai.PermissionDeniedError,'model_unavailable',503),
           (openai.NotFoundError,'model_unavailable',503),(openai.RateLimitError,'rate_limited',429),
           (openai.APITimeoutError,'timeout',504),(openai.APIConnectionError,'connection_error',502),
           (openai.BadRequestError,'invalid_provider_request',502)]
    code,status=next(((code,status) for kind,code,status in rules if isinstance(exc,kind)),('provider_unavailable',502))
    messages={'invalid_credentials':'The selected provider rejected its API key.','model_unavailable':'The configured model is unavailable to this API account.',
        'rate_limited':'The selected provider rate limit or quota was reached.','timeout':'The selected provider timed out.',
        'connection_error':'Cannot connect to the selected provider.','invalid_provider_request':'The selected provider rejected the request format.',
        'provider_unavailable':'The selected provider request failed.'}
    return AIProviderError(code,messages[code]+' No provider fallback was used.',status)
