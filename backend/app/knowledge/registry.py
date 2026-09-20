import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
from app.knowledge.contracts import SourceSpec, KnowledgeError

def source_set(name='hk_core') -> list[SourceSpec]:
    if name != 'hk_core':
        raise KnowledgeError('Only the controlled hk_core source set is supported.')
    return [SourceSpec.model_validate(x) for x in json.loads(Path(__file__).with_name('hk_core.json').read_text(encoding='utf-8'))]

def official_url(url: str):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname != 'www.labour.gov.hk' or parsed.port not in (None,443)
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or '..' in unquote(parsed.path).split('/') or not parsed.path.startswith('/eng/public/')):
        raise KnowledgeError('Source URL is not an approved official Labour Department publication URL.')

def require_registered(spec: SourceSpec):
    official_url(spec.source_url)
    official_url(spec.catalog_url)
    if not any(x == spec for x in source_set()):
        raise KnowledgeError('Source registration must match the reviewed hk_core manifest; arbitrary sources cannot be verified.')
