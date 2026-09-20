from typing import Protocol, Annotated, Literal
from fastapi import Header, Depends
from app.schemas.contracts import InspectionAnalysis, ReinspectionAnalysis, ReinspectionContext


class SafetyAIProvider(Protocol):
    model_provider: str
    model_name: str
    prompt_version: str

    def analyze_inspection(self, *, location: str, description: str | None, image_path: str | None) -> InspectionAnalysis: ...

    def analyze_reinspection(self, *, incident_id: int, previous_risk: int, evidence_path: str | None, notes: str, original_hazard: ReinspectionContext | None = None) -> ReinspectionAnalysis: ...


def create_safety_provider(config, kind='vision', language='en', client=None):
    from app.ai.capabilities import workload
    from app.ai.mock import MockSafetyAIProvider
    from app.ai.real import RealMultimodalSafetyAIProvider
    from app.ai.deepseek import DeepSeekSafetyAIProvider
    name,model=workload(config,kind)
    registry={'mock':MockSafetyAIProvider,'openai':RealMultimodalSafetyAIProvider,'deepseek':DeepSeekSafetyAIProvider}
    provider=registry[name]() if name=='mock' else registry[name](config.model_copy(update={'vision_model':model}),client)
    provider.output_language=language
    return provider


def get_provider(language: Annotated[Literal['en','zh-CN'], Header(alias='X-SafeSite-Language')] = 'en') -> SafetyAIProvider:
    from app.core.config import settings
    return create_safety_provider(settings,'vision',language)


# Preserve the legacy dependency override when no separate reinspection configuration is set.
def get_reinspection_provider(vision: Annotated[SafetyAIProvider, Depends(get_provider)],
        language: Annotated[Literal['en','zh-CN'], Header(alias='X-SafeSite-Language')] = 'en') -> SafetyAIProvider:
    from app.core.config import settings
    if settings.reinspection_provider is None and settings.reinspection_model is None:return vision
    return create_safety_provider(settings,'reinspection',language)
