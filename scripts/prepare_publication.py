"""Offline, fail-closed publication inventory of this existing project. Never uploads.

Originals are read only. Review copies redact local user paths/reviewer identities.
Generated artifacts stay under ignored .publication/. No Git metadata is copied.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.publication'
PRUNE = {'.git', '.publication', 'node_modules', '.venv', '.next', '__pycache__',
         '.pytest_cache', 'test-results', 'playwright-report', 'data', 'uploads'}
TEXT = {'.py', '.md', '.json', '.jsonl', '.html', '.ts', '.tsx', '.css', '.mjs',
        '.cjs', '.ps1', '.txt', '.ini', '.example', '.yml', '.yaml', '.toml', '.xml'}
MEDIA = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf', '.mp4', '.zip', '.onnx'}
PATTERNS = {
    'provider_token_pattern': re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{24,}'),
    'github_token_pattern': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential_in_url': re.compile(rb'https?://[^\s/:<>"\x27]+:[^\s/@<>"\x27]+@'),
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def configured_secrets():
    # Values are used only for byte comparison and never written or printed.
    values = []
    for p in (ROOT / 'backend/.env', ROOT / 'frontend/.env.local'):
        if not p.exists():
            continue
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            if '=' not in line or line.lstrip().startswith('#'):
                continue
            key, value = line.split('=', 1)
            value = value.strip().strip('\"\x27')
            if re.search(r'KEY|TOKEN|PASSWORD|SECRET', key, re.I) and len(value) >= 8:
                values.append(value.encode())
    return values

def findings(data, secrets):
    result = [name for name, pattern in PATTERNS.items() if pattern.search(data)]
    if any(value in data for value in secrets):
        result.append('configured_secret_match')
    return result

def classify(path):
    if path.name.startswith('.env') and path.name != '.env.example':
        return 'exclude', 'private environment'
    if path.suffix.lower() in MEDIA:
        return 'hold', 'media redistribution/privacy review; original retained'
    if path.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.pem', '.key', '.p12', '.pfx'}:
        return 'exclude', 'private database or credential container'
    if path.suffix.lower() in {'.log', '.pyc', '.tsbuildinfo', '.lock'}:
        return 'exclude', 'runtime/cache/lock artifact'
    if 'preservation' in path.name or path.name == 'day1-preservation.json':
        return 'exclude', 'local integrity receipt; may contain private environment digest'
    if path.suffix in TEXT or path.name in {'.gitignore', 'LICENSE', 'NOTICE'}:
        return 'include', 'project source/documentation/evaluation/configuration'
    return 'hold', 'unrecognized file requires manual review'

def reviewer_names():
    names = set()
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {'reviewer', 'secondary_reviewer'} and isinstance(item, str) and item.strip():
                    names.add(item.strip())
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    for p in (ROOT / 'evaluation/datasets').glob('vision*.json'):
        walk(json.loads(p.read_text(encoding='utf-8-sig')))
    return sorted(names, key=len, reverse=True)

def sanitize(data, names):
    text = data.decode('utf-8-sig')
    # Match raw Markdown paths as well as JSON-escaped Windows paths.
    text = re.sub(r'[A-Za-z]:[\\/]+Users[\\/]+[^\\/\r\n"<>]+', '[LOCAL_HOME]', text)
    text = re.sub(r'[LOCAL_HOME]/\s"<>]+|[LOCAL_HOME]/\s"<>]+', '[LOCAL_HOME]', text)
    for index, name in enumerate(names, 1):
        text = text.replace(name, f'REVIEWER_{index}')
        text = text.replace(json.dumps(name, ensure_ascii=True)[1:-1], f'REVIEWER_{index}')
    encoded = text.encode('utf-8')
    return (b'\xef\xbb\xbf' + encoded) if data.startswith(b'\xef\xbb\xbf') else encoded

def git_audit(secrets):
    gitroot = ROOT.parent
    base = ['git', '-c', f'safe.directory={gitroot.as_posix()}', '-C', str(ROOT)]
    def run(*args):
        return subprocess.run(base + list(args), capture_output=True, check=True).stdout
    commits = int(run('rev-list', '--all', '--count'))
    tracked = run('ls-files', '-z').split(b'\0')
    objects = run('cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines()
    alerts = []
    counts = {}
    # Scan all objects, including unreachable blobs, without printing their content.
    proc = subprocess.Popen(base + ['cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for item in objects:
            oid, kind, size = item.split()
            counts[kind] = counts.get(kind, 0) + 1
            proc.stdin.write((oid + '\n').encode()); proc.stdin.flush()
            header = proc.stdout.readline().split()
            content = proc.stdout.read(int(header[2])); proc.stdout.read(1)
            hits = findings(content, secrets)
            if hits:
                alerts.append({'object': oid, 'type': kind, 'findings': hits})
    finally:
        proc.stdin.close(); proc.wait()
    fsck = subprocess.run(base + ['fsck', '--full'], capture_output=True)
    lines = (fsck.stdout + fsck.stderr).decode(errors='replace').splitlines()
    return {'repository_scope': 'parent workspace; SafeSite has no separate .git',
            'reachable_commits': commits, 'tracked_files_under_project': len([x for x in tracked if x]),
            'objects_scanned': len(objects), 'object_types': counts, 'secret_findings': alerts,
            'fsck_exit_code': fsck.returncode, 'dangling_not_corrupt_count': sum(x.startswith('dangling ') for x in lines),
            'history_will_be_uploaded': False}

def main():
    OUT.mkdir(exist_ok=True)
    secrets, names = configured_secrets(), reviewer_names()
    inventory, archive_data, excluded_dirs = [], {}, []
    approved_media = {r['path']: r for r in json.loads((ROOT / 'docs/PUBLICATION_MEDIA.json').read_text(encoding='utf-8'))}
    for base, dirs, files in os.walk(ROOT, followlinks=False):
        for directory in list(dirs):
            p = Path(base) / directory
            if directory in PRUNE or p.is_symlink() or p.is_junction():
                dirs.remove(directory)
                excluded_dirs.append(p.relative_to(ROOT).as_posix())
        for filename in sorted(files):
            p = Path(base) / filename
            rel = p.relative_to(ROOT).as_posix()
            action, reason = classify(p)
            if p.is_symlink():
                action, reason = 'exclude', 'symlink target not published'
            raw = p.read_bytes()
            licensed_media = rel in approved_media and digest(raw) == approved_media[rel]['sha256']
            if licensed_media:
                action, reason = 'include', 'file-specific archived public-domain/CC evidence; attribution in THIRD_PARTY_MATERIALS.md'
            row = {'path': rel, 'decision': action, 'reason': reason, 'bytes': len(raw)}
            if action == 'include':
                hits = findings(raw, secrets)
                if hits:
                    row.update(decision='hold', reason='secret-pattern review', findings=hits)
                else:
                    try:
                        public = raw if licensed_media else sanitize(raw, names)
                    except UnicodeDecodeError:
                        row.update(decision='hold', reason='unexpected binary encoding')
                    else:
                        row.update(source_sha256=digest(raw), publication_sha256=digest(public),
                                   privacy_redacted=(raw != public))
                        archive_data[rel] = public
            inventory.append(row)
    history = git_audit(secrets)
    result = {'status': 'LOCAL PROPOSAL ONLY; explicit public-release approval required',
              'inventory': sorted(inventory, key=lambda x:x['path']), 'excluded_directories': sorted(excluded_dirs),
              'git_audit': history, 'included_count': len(archive_data),
              'held_count': sum(r['decision']=='hold' for r in inventory),
              'excluded_file_count': sum(r['decision']=='exclude' for r in inventory),
              'privacy_redacted_count': sum(r.get('privacy_redacted', False) for r in inventory),
              'api_calls': 0}
    (OUT/'inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with zipfile.ZipFile(OUT/'SafeSite-Intelligence-review.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(archive_data.items()):
            z.writestr(name, data)
    with zipfile.ZipFile(OUT/'SafeSite-Intelligence-review.zip') as z:
        assert z.testzip() is None
        assert all(not findings(z.read(n), secrets) for n in z.namelist())
        assert set(z.namelist()) == set(archive_data)
    counts = {}
    for name in archive_data:
        section = name.split('/')[0]
        counts[section] = counts.get(section, 0) + 1
    print(json.dumps({k:result[k] for k in ['included_count','held_count','excluded_file_count','privacy_redacted_count']}))
    print(json.dumps({'sections': counts, 'git_audit': history}))

if __name__ == '__main__':
    main()
