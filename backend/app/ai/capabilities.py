"""Reviewed hosted-model capabilities, verified 2026-09-15. Unknown models fail closed."""
from app.ai.errors import AIProviderError

OPENAI_MODELS=('gpt-5.6-terra','gpt-5.6-sol')
CAPABILITIES={
 **{('openai',model):dict(text=True,image_input=True,structured_json=True,strict_schema=True,tools=True,usage=True,
     source='https://developers.openai.com/api/docs/models/'+model) for model in OPENAI_MODELS},
 **{('deepseek',model):dict(text=True,image_input=model=='deepseek-flash',structured_json=True,strict_schema=False,tools=True,usage=True,
     source='https://api-docs.deepseek.com/quick_start/pricing/') for model in ('deepseek-flash','deepseek-v4-pro')},
}

def workload(config,kind):
    if kind=='analyst':return config.analyst_provider,config.analyst_model
    vision=config.vision_provider or ('mock' if config.ai_provider=='mock' else 'openai')
    provider=(config.reinspection_provider or vision) if kind=='reinspection' else vision
    model=(config.reinspection_model or config.vision_model) if kind=='reinspection' else config.vision_model
    return provider,'safesite-scenario-v1' if provider=='mock' else model

def key_for(config,provider):
    return config.deepseek_api_key if provider=='deepseek' else config.openai_api_key

def validate(provider,model,kind):
    if provider in ('mock','deterministic'):return
    capability=CAPABILITIES.get((provider,model))
    if not capability:raise AIProviderError('unsupported_model','The configured provider/model has no reviewed capability entry. Update the capability registry from official documentation before use.',503)
    if kind in ('vision','reinspection') and not capability['image_input']:
        raise AIProviderError('unsupported_image_capability','The configured model does not support image input. Select an image-capable model for this workload; no fallback was used.',503)

def readiness(config,kind):
    provider,model=workload(config,kind)
    try:
        validate(provider,model,kind)
        if provider not in ('mock','deterministic'):
            key=key_for(config,provider)
            if not key or not key.get_secret_value().strip():
                raise AIProviderError('missing_credentials',('DEEPSEEK_API_KEY' if provider=='deepseek' else 'OPENAI_API_KEY')+' is required for this workload. No provider fallback was used.',503)
        error=None
    except AIProviderError as exc:error=exc.message
    return dict(provider=provider,model=model,ready=error is None,error=error,capabilities=CAPABILITIES.get((provider,model)),capabilities_verified_at='2026-09-15')
