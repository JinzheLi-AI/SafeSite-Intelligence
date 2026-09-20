from app.core.config import Settings
from app.ai.capabilities import workload


def test_legacy_openai_alias_keeps_explicit_vision_model():
    config=Settings(_env_file=None,SAFESITE_AI_PROVIDER='openai',SAFESITE_VISION_PROVIDER='openai',
        SAFESITE_VISION_MODEL='gpt-5.6-sol',SAFESITE_ANALYST_PROVIDER='deterministic')
    assert config.ai_provider=='real'
    assert workload(config,'vision')==('openai','gpt-5.6-sol')
    assert config.analyst_provider=='deterministic'


def test_legacy_openai_alias_does_not_override_explicit_mock():
    config=Settings(_env_file=None,SAFESITE_AI_PROVIDER='openai',SAFESITE_VISION_PROVIDER='mock')
    assert workload(config,'vision')==('mock','safesite-scenario-v1')
