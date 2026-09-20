"""Local-only manual pilot labeling. No model or product imports."""
import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import tempfile
from urllib.parse import unquote, urlparse, parse_qs

try:
    from .validate_vision_dataset import validate_dataset, IMAGE_ROOT
except ImportError:
    from validate_vision_dataset import validate_dataset, IMAGE_ROOT

MANIFEST = IMAGE_ROOT / 'datasets/vision_pilot_20.json'
EDITABLE = {'ground_truth_hazards', 'ambiguous', 'expected_human_review', 'evidence_notes',
            'reviewer', 'secondary_reviewer', 'source', 'license_or_provenance', 'group'}


def read_manifest(path):
    content = Path(path).read_bytes()
    rows = json.loads(content.decode('utf-8-sig'))
    return rows, hashlib.sha256(content).hexdigest()


@contextmanager
def save_lock(path):
    lock = Path(str(path) + '.labeling.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Another save is active. Retry after it finishes. If interrupted, see the launch guide for stale-lock recovery.') from None
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def save_review(path, case_id, fields, expected_revision, image_root=IMAGE_ROOT):
    """Validate and atomically update one row, rejecting stale tabs and protected fields."""
    path = Path(path)
    if path.resolve() == MANIFEST.resolve():
        raise ValueError('Historical pilot is read-only.')
    if not isinstance(fields, dict) or set(fields) != EDITABLE:
        raise ValueError('Supply only the manual review fields; image paths, hashes and case IDs cannot be edited.')
    if not isinstance(expected_revision, str):
        raise ValueError('Reload the dataset before saving.')
    for name in ['reviewer', 'evidence_notes']:
        if not isinstance(fields[name], str) or not fields[name].strip():
            raise ValueError(name.replace('_', ' ').capitalize() + ' is required.')
    for name in ['ambiguous', 'expected_human_review']:
        if type(fields[name]) is not bool:
            raise ValueError('Explicitly choose Yes or No for ' + name.replace('_', ' ') + '.')
    if not isinstance(fields['ground_truth_hazards'], list):
        raise ValueError('Hazards must be a list; [] is allowed for a reviewed negative.')
    with save_lock(path):
        rows, revision = read_manifest(path)
        if revision != expected_revision:
            raise ValueError('The manifest changed since it was loaded. Reload before saving; your changes were not written.')
        matches = [row for row in rows if row.get('case_id') == case_id]
        if len(matches) != 1:
            raise ValueError('Case ID is missing or duplicated.')
        row = matches[0]
        row.update({key: value.strip() if isinstance(value, str) else value for key, value in fields.items()})
        row['label_status'] = 'reviewed'
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                             prefix='.label-review-', suffix='.json', delete=False) as temporary:
                temp_path = Path(temporary.name)
                json.dump(rows, temporary, indent=2, ensure_ascii=False)
                temporary.write('\n'); temporary.flush(); os.fsync(temporary.fileno())
            validation = validate_dataset(temp_path, image_root)
            if validation['errors']:
                raise ValueError('\n'.join(validation['errors']))
            # Detect non-tool edits while validating; lock coordinates labeling-tool instances.
            if read_manifest(path)[1] != revision:
                raise ValueError('Manifest changed during validation. Reload before saving.')
            os.replace(temp_path, path)
            return validation
        finally:
            if temp_path is not None: temp_path.unlink(missing_ok=True)


def make_handler(manifest=MANIFEST, image_root=IMAGE_ROOT, token=None, datasets=None):
    manifest, image_root = Path(manifest), Path(image_root).resolve()
    token = token or secrets.token_urlsafe(32)
    try:
        from .annotation_store import DatasetStore, rows, frozen
    except ImportError:
        from annotation_store import DatasetStore, rows, frozen
    if datasets is None:
        datasets = {'historical': manifest}
        if manifest.resolve() == MANIFEST.resolve():
            datasets.update(development=IMAGE_ROOT/'datasets/vision_v2_development_v1.json', heldout=IMAGE_ROOT/'datasets/vision_v2_heldout_v1.json')
    store = DatasetStore(image_root, datasets, save_lock)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def local_request(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            origin = self.headers.get('Origin')
            return self.headers.get('Host') == expected and (origin is None or origin == 'http://' + expected)

        def send_content(self, status, body, content_type='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers(); self.wfile.write(body)

        def json_response(self, status, value):
            self.send_content(status, json.dumps(value).encode('utf-8'))

        def dataset_key(self):
            key = parse_qs(urlparse(self.path).query).get('dataset', ['historical'])[0]
            store.path(key)
            return key

        def do_GET(self):
            if not self.local_request():
                return self.json_response(403, {'error': 'Local origin required.'})
            route = urlparse(self.path).path
            try:
                if route == '/':
                    return self.send_content(200, Path(__file__).with_suffix('.html').read_bytes(), 'text/html; charset=utf-8')
                if route == '/datasets':
                    return self.json_response(200, {'datasets': list(datasets)})
                if route == '/dataset':
                    key=self.dataset_key();doc,revision=store.load(key)
                    return self.json_response(200, {'cases': rows(doc), 'revision': revision, 'token': token,
                        'dataset':key,'readonly':key=='historical' or isinstance(doc,list) or frozen(doc),
                        'metadata':{} if isinstance(doc,list) else {k:v for k,v in doc.items() if k!='cases'},
                        'validation': validate_dataset(store.path(key), image_root) if isinstance(doc,list) else store.validate(key)})
                if route == '/guide':
                    guide = IMAGE_ROOT.parent / 'docs' / ('VISION_LABELING_GUIDE.md' if self.dataset_key()=='historical' else 'VISION_LABEL_PROTOCOL_V2.md')
                    return self.send_content(200, guide.read_bytes(), 'text/plain; charset=utf-8')
                if route.startswith('/image/'):
                    from PIL import Image
                    doc, _ = store.load(self.dataset_key())
                    row = next(r for r in rows(doc) if r['case_id'] == unquote(route[len('/image/'):]))
                    path = (image_root / row['image_path']).resolve()
                    if not path.is_relative_to(image_root): raise ValueError('Image outside image root.')
                    data = path.read_bytes()
                    with Image.open(BytesIO(data)) as image:
                        media = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}[image.format]
                        image.verify()
                    return self.send_content(200, data, media)
                return self.json_response(404, {'error': 'Not found.'})
            except (OSError, ValueError, KeyError, TypeError, StopIteration):
                return self.json_response(400, {'error': 'Could not load the manifest or registered image.'})

        def do_POST(self):
            if not self.local_request() or self.headers.get('X-Label-Token') != token:
                return self.json_response(403, {'error': 'Reload this local page before saving.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                route=urlparse(self.path).path
                if not 0 < size <= (14_100_000 if route=='/import' else 100_000): raise ValueError('Invalid request size.')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict): raise ValueError('Invalid request.')
                key=self.dataset_key()
                if route == '/validate':
                    doc,_=store.load(key)
                    return self.json_response(200, validate_dataset(store.path(key),image_root) if isinstance(doc,list) else store.validate(key))
                if route == '/save':
                    validation=store.save(key,data.get('case_id'),data.get('fields'),data.get('revision'))
                elif route == '/import':
                    validation=store.upload(key,data.get('case_id'),data.get('image_base64'),data.get('revision'))
                elif route == '/freeze':
                    validation=store.freeze(key,data.get('revision'),data.get('acknowledged'))
                else: return self.json_response(404, {'error':'Not found.'})
                return self.json_response(200, {'validation':validation})
            except (OSError, ValueError, TypeError) as exc:
                return self.json_response(400, {'error': str(exc)})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--image-root', type=Path, default=IMAGE_ROOT)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(args.manifest, args.image_root))
    print(f'Local manual labeling: http://127.0.0.1:{server.server_port}', flush=True)
    print('Historical pilot read-only; V2 development and held-out editable until frozen. No model calls.', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()
