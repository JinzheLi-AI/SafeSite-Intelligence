from functools import lru_cache
import math
from app.core.config import settings
from app.knowledge.contracts import KnowledgeError

def signature() -> str:
    return settings.embedding_provider + ':' + settings.embedding_model

@lru_cache(maxsize=2)
def local_model(model: str, cache: str, allow_download: bool):
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=model, cache_dir=cache, threads=2, local_files_only=not allow_download)

class Embedder:
    @property
    def signature(self):
        return signature()

    def encode(self, texts: list[str], *, query=False, allow_download=False) -> list[list[float]]:
        try:
            if settings.embedding_provider == 'fastembed':
                model = local_model(settings.embedding_model, str(settings.embedding_cache_dir), allow_download)
                values = list(model.query_embed(texts) if query else model.passage_embed(texts, batch_size=32))
                result = [x.tolist() for x in values]
            else:
                from openai import OpenAI
                key = settings.openai_api_key
                if not key or not key.get_secret_value().strip():
                    raise KnowledgeError('OpenAI embeddings require OPENAI_API_KEY; verified retrieval is unavailable.')
                with OpenAI(api_key=key.get_secret_value(), base_url='https://api.openai.com/v1', timeout=30, max_retries=0) as client:
                    response = client.embeddings.create(model=settings.embedding_model, input=texts)
                    result = [item.embedding for item in sorted(response.data, key=lambda x:x.index)]
            validate_vectors(result, len(texts))
            return result
        except KnowledgeError:
            raise
        except Exception as exc:
            raise KnowledgeError('Embedding setup/request failed (' + type(exc).__name__ + '). Run the ingestion CLI to download the local model, or check remote credentials/model configuration.') from None

def validate_vectors(vectors, count):
    if len(vectors) != count or not vectors:
        raise KnowledgeError('Embedding count does not match the input.')
    dim = len(vectors[0])
    if dim < 2 or any(len(v) != dim or not all(math.isfinite(float(x)) for x in v)
                      or sum(float(x)**2 for x in v) == 0 for v in vectors):
        raise KnowledgeError('Invalid embedding dimensions or values.')
