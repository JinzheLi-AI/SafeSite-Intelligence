from pathlib import Path
from typing import Literal
from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', populate_by_name=True)
    app_name: str = 'SafeSite Intelligence'
    database_url: str = 'sqlite:///./data/safesite.db'
    cors_origins: list[str] = ['http://localhost:3000', 'http://127.0.0.1:3000']
    auto_seed: bool = True
    upload_dir: Path = Path('./uploads')
    max_upload_bytes: int = 10 * 1024 * 1024
    ai_provider: Literal['mock', 'real'] = Field(default='mock',
        validation_alias=AliasChoices('SAFESITE_AI_PROVIDER', 'AI_PROVIDER'))
    @field_validator('ai_provider', mode='before')
    @classmethod
    def normalize_legacy_openai(cls, value):
        # Accept the explicit provider name without changing legacy mock/real semantics.
        return 'real' if value == 'openai' else value

    vision_provider: Literal['mock', 'openai', 'deepseek'] | None = Field(default=None, validation_alias='SAFESITE_VISION_PROVIDER')
    reinspection_provider: Literal['mock', 'openai', 'deepseek'] | None = Field(default=None, validation_alias='SAFESITE_REINSPECTION_PROVIDER')
    reinspection_model: str | None = Field(default=None, validation_alias='SAFESITE_REINSPECTION_MODEL')
    deepseek_api_key: SecretStr | None = Field(default=None, validation_alias='DEEPSEEK_API_KEY')
    pricing_file: Path = Field(default=Path(__file__).with_name('provider_pricing.json'), validation_alias='SAFESITE_PRICING_FILE')
    openai_api_key: SecretStr | None = Field(default=None, validation_alias='OPENAI_API_KEY')
    vision_model: str = Field(default='gpt-5.6-terra', min_length=1, max_length=100,
        validation_alias='SAFESITE_VISION_MODEL')
    vision_prompt_version: Literal['vision-v1', 'vision-v2'] = Field(default='vision-v1', validation_alias='SAFESITE_VISION_PROMPT_VERSION')
    ai_timeout_seconds: float = Field(default=90, ge=1, le=180, validation_alias='SAFESITE_AI_TIMEOUT_SECONDS')
    ai_max_output_tokens: int = Field(default=6000, ge=1000, le=16000, validation_alias='SAFESITE_AI_MAX_OUTPUT_TOKENS')

    analyst_provider: Literal['deterministic', 'openai', 'deepseek'] = Field(default='deterministic', validation_alias='SAFESITE_ANALYST_PROVIDER')
    analyst_model: str = Field(default='gpt-5.6-terra', min_length=1, max_length=100, validation_alias='SAFESITE_ANALYST_MODEL')
    analyst_timeout_seconds: float = Field(default=30, ge=1, le=60, validation_alias='SAFESITE_ANALYST_TIMEOUT_SECONDS')

    embedding_provider: Literal['fastembed', 'openai'] = Field(default='fastembed', validation_alias='SAFESITE_EMBEDDING_PROVIDER')
    embedding_model: str = Field(default='BAAI/bge-small-en-v1.5', validation_alias='SAFESITE_EMBEDDING_MODEL')
    embedding_cache_dir: Path = Field(default=Path('./data/knowledge/models'), validation_alias='SAFESITE_EMBEDDING_CACHE_DIR')
    knowledge_source_dir: Path = Field(default=Path('./data/knowledge/sources'), validation_alias='SAFESITE_KNOWLEDGE_SOURCE_DIR')
    retrieval_min_semantic: float = Field(default=0.55, ge=0, le=1, validation_alias='SAFESITE_RETRIEVAL_MIN_SEMANTIC')
    retrieval_min_score: float = Field(default=0.55, ge=0, le=1, validation_alias='SAFESITE_RETRIEVAL_MIN_SCORE')


settings = Settings()
