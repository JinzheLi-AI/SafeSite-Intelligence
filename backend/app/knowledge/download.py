import hashlib
import json
import time
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, unquote
import httpx
from app.db.session import utcnow
from app.knowledge.registry import require_registered, official_url
from app.knowledge.contracts import SourceSpec, KnowledgeError

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.extend(value for key, value in attrs if key == 'href' and value)

def fetch(spec: SourceSpec, directory: Path) -> tuple[bytes, str, object]:
    require_registered(spec)
    # TLS verification remains enabled. Redirects are rejected, never followed to another domain.
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        catalog = client.get(spec.catalog_url)
        catalog.raise_for_status()
        if len(catalog.content) > 2_000_000:
            raise KnowledgeError('Official catalogue exceeds size limit.')
        links = Links()
        links.feed(catalog.text)
        if unquote(spec.source_url) not in {unquote(urljoin(spec.catalog_url, u)) for u in links.urls}:
            raise KnowledgeError('Registered PDF is no longer linked by the official catalogue; review registration.')
        data = bytearray()
        start = time.monotonic()
        with client.stream('GET', spec.source_url) as response:
            response.raise_for_status()
            official_url(str(response.url))
            if response.status_code != 200 or 'pdf' not in response.headers.get('content-type','').lower():
                raise KnowledgeError('Official source did not return a PDF.')
            for block in response.iter_bytes(65536):
                data.extend(block)
                if len(data) > 30 * 1024 * 1024 or time.monotonic() - start > 90:
                    raise KnowledgeError('Source download exceeded the 30 MB / 90 second limit.')
    if not data.startswith(b'%PDF-'):
        raise KnowledgeError('Source content is not a PDF.')
    checksum = hashlib.sha256(data).hexdigest()
    retrieved_at = utcnow()
    directory.mkdir(parents=True, exist_ok=True)
    filename = spec.key + '-' + checksum + '.pdf'
    (directory / filename).write_bytes(data)
    (directory / (filename + '.json')).write_text(json.dumps({
        'source_url': spec.source_url, 'catalog_url': spec.catalog_url,
        'retrieved_at': retrieved_at.isoformat(), 'sha256': checksum}, indent=2), encoding='utf-8')
    return bytes(data), checksum, retrieved_at
