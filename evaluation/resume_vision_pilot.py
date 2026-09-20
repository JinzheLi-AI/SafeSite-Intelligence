"""Bounded one-pass pilot run; report-only mode never imports providers."""
import argparse
import base64
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MANIFEST = ROOT / 'evaluation/datasets/vision_pilot_20.json'
OUTPUT = ROOT / 'evaluation/reports/vision_openai_sol_20'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)

def already_attempted(rows, case_id):
    return any(r['case_id'] == case_id and r.get('requests_attempted', 0) for r in rows)

def execute(checkpoint=False):
    from evaluation.validate_vision_dataset import validate_dataset
    validation = validate_dataset(MANIFEST)
    if validation['errors'] or validation['benchmark_ready'] != 20:
        raise RuntimeError('Dataset gate failed')
    sys.path.insert(0, str(ROOT / 'backend'))
    os.chdir(ROOT / 'backend')
    from app.core.config import settings
    from app.ai.real import RealMultimodalSafetyAIProvider
    from app.ai.images import image_data_url
    from app.ai.prompts import VISION_PROMPT_VERSION
    from app.ai.errors import AIProviderError
    from PIL import Image
    from io import BytesIO
    assert settings.vision_provider == 'openai' and settings.vision_model == 'gpt-5.6-sol'
    assert settings.openai_api_key and settings.openai_api_key.get_secret_value().strip()
    assert VISION_PROMPT_VERSION == 'vision-v1'
    frozen = MANIFEST.read_bytes()
    cases = json.loads(frozen)
    env_hash = digest(Path('.env').read_bytes())
    prompt_hash = digest((ROOT / 'backend/app/ai/prompts.py').read_bytes())
    old_root = settings.upload_dir
    preprocessed = {}
    try:
        for case in cases:
            path = ROOT / 'evaluation' / case['image_path']
            settings.upload_dir = path.parent
            url = image_data_url('/uploads/' + path.name)
            data = base64.b64decode(url.split(',', 1)[1])
            with Image.open(BytesIO(data)) as im:
                dims = list(im.size)
            preprocessed[case['case_id']] = dict(processed_sha256=digest(data), processed_dimensions=dims, processed_bytes=len(data))
    finally:
        settings.upload_dir = old_root
    OUTPUT.mkdir(parents=True, exist_ok=True)
    run = dict(schema_version='vision-pilot-single-pass-v1', started_at=datetime.now(timezone.utc).isoformat(),
               manifest_sha256=digest(frozen), prompt_file_sha256=prompt_hash, manifest_snapshot=cases,
               provider='openai', requested_model='gpt-5.6-sol', prompt_version='vision-v1',
               planned_requests=20, maximum_requests=20, requests_attempted=0, sdk_retries=0, validation_attempts=1,
               preflight=validation, billing_precheck='No separate billing endpoint available; first authorized inference gates access.',
               status='running', stop_reason=None, cases=[])
    cache = OUTPUT / 'raw_results.json'
    if cache.exists():
        prior = json.loads(cache.read_text(encoding='utf-8'))
        assert prior['manifest_sha256'] == digest(frozen)
        assert prior['prompt_file_sha256'] == prompt_hash
        assert not prior.get('stop_reason'), 'Stopped run requires explicit investigation; no automatic restart.'
        if not checkpoint:
            first = next((r for r in prior['cases'] if r['case_id'] == cases[0]['case_id']), {})
            assert first.get('provider_success'), 'Checkpoint must succeed before continuing.'
        run = prior
    run['run_id'] = OUTPUT.name
    run['preprocessed'] = preprocessed
    run['status'] = 'running'
    def save():
        write_json(cache, run)
    save()
    consecutive_network_failures = 0
    try:
        for case in cases:
            existing = next((r for r in run['cases'] if r['case_id'] == case['case_id']), None)
            if already_attempted(run['cases'], case['case_id']):
                continue  # Includes uncertain/interrupted attempts: never recharge them.
            if run['stop_reason'] or (checkpoint and run['requests_attempted'] >= 1):
                continue
            if existing:
                run['cases'].remove(existing)
            assert MANIFEST.read_bytes() == frozen
            path = ROOT / 'evaluation' / case['image_path']
            assert digest(path.read_bytes()) == case['image_hash']
            settings.upload_dir = path.parent
            row = dict(case, **preprocessed[case['case_id']], provider='openai', requested_model='gpt-5.6-sol',
                       actual_model=None, prompt_version='vision-v1', provider_success=False, provider_error=None,
                       requests_attempted=0, predicted_hazards=None, hazard_confidences=None, overall_confidence=None,
                       requires_human_review=None, visual_evidence=None, latency_ms=None,
                       input_tokens=None, output_tokens=None, total_tokens=None, estimated_cost_usd=None)
            run['cases'].append(row)
            save()
            provider = RealMultimodalSafetyAIProvider()
            provider.validation_attempts = 1
            client = provider._create_client()
            assert client.max_retries == 0
            def before(request):
                assert request.method == 'POST' and str(request.url) == 'https://api.openai.com/v1/responses'
                assert run['requests_attempted'] < 20 and row['requests_attempted'] == 0
                body = json.loads(request.content)
                assert body['model'] == 'gpt-5.6-sol'
                images = [p for item in body['input'] if isinstance(item.get('content'), list) for p in item['content'] if p.get('type') == 'input_image']
                assert len(images) == 1
                assert digest(base64.b64decode(images[0]['image_url'].split(',', 1)[1])) == row['processed_sha256']
                row['system_prompt_sha256'] = digest(body['input'][0]['content'].encode())
                previous = [r['system_prompt_sha256'] for r in run['cases'][:-1] if 'system_prompt_sha256' in r]
                assert all(p == row['system_prompt_sha256'] for p in previous)
                row['image_bytes_verified_in_request'] = True
                row['provider_error'] = 'in_flight_outcome_unknown'
                row['requests_attempted'] = 1
                run['requests_attempted'] += 1
                save()
            def after(response):
                row['http_status'] = response.status_code
            client._client.event_hooks['request'] = [before]
            client._client.event_hooks['response'] = [after]
            provider._injected_client = client
            started = time.perf_counter()
            try:
                answer = provider.analyze_inspection(location='', description=None, image_path='/uploads/' + path.name)
                raw = provider.last_visual_output.model_dump(mode='json')
                row.update(provider_success=True, provider_error=None, normalized_result=answer.model_dump(mode='json'), raw_visual_output=raw,
                           predicted_hazards=sorted({h['hazard_type'] for h in raw['hazards']}),
                           hazard_confidences=[dict(hazard_type=h['hazard_type'], confidence=h['confidence']) for h in raw['hazards']],
                           overall_confidence=answer.overall_confidence, requires_human_review=answer.requires_human_review,
                           model_requires_human_review=raw['requires_human_review'],
                           visual_evidence=[dict(hazard_type=h['hazard_type'], evidence=h['visual_evidence'], description=h['description']) for h in raw['hazards']])
                consecutive_network_failures = 0
            except Exception as exc:
                code = getattr(exc, 'code', type(exc).__name__)
                row['provider_error'] = code
                consecutive_network_failures = consecutive_network_failures + 1 if code in {'connection_error', 'timeout'} else 0
                if code in {'invalid_credentials', 'missing_credentials', 'model_unavailable', 'rate_limited', 'invalid_provider_request'}:
                    run['stop_reason'] = code
                elif code == 'invalid_output' and any(r.get('provider_error') == 'invalid_output' for r in run['cases'][:-1]):
                    run['stop_reason'] = 'systematic_schema_failure'
                elif consecutive_network_failures >= 2:
                    run['stop_reason'] = 'two_consecutive_network_failures'
                if run['requests_attempted'] == 1:
                    run['stop_reason'] = 'checkpoint_failed:' + code
            finally:
                row['elapsed_ms'] = round((time.perf_counter() - started) * 1000)
                client.close()
                row['call_records'] = provider.call_records
                if provider.call_records:
                    record = provider.call_records[0]
                    for key in ['input_tokens', 'output_tokens', 'total_tokens', 'latency_ms', 'estimated_cost_usd']:
                        row[key] = record.get(key)
                    row['actual_model'] = record.get('returned_model')
                save()
            print(json.dumps(dict(case_id=case['case_id'], success=row['provider_success'], error=row['provider_error'], requests=run['requests_attempted'])), flush=True)
    finally:
        settings.upload_dir = old_root
        run['manifest_unchanged'] = MANIFEST.read_bytes() == frozen
        run['images_unchanged'] = all(digest((ROOT / 'evaluation' / c['image_path']).read_bytes()) == c['image_hash'] for c in cases)
        run['env_unchanged'] = digest(Path('.env').read_bytes()) == env_hash
        run['prompt_unchanged'] = digest((ROOT / 'backend/app/ai/prompts.py').read_bytes()) == prompt_hash
        for case in cases:
            if not any(r['case_id'] == case['case_id'] for r in run['cases']):
                run['cases'].append(dict(case, provider='openai', requested_model='gpt-5.6-sol', prompt_version='vision-v1', provider_success=False, provider_error='not_attempted', requests_attempted=0))
        run['cases'].sort(key=lambda r: r['case_id'])
        run['completed_at'] = datetime.now(timezone.utc).isoformat()
        run['status'] = 'stopped' if run['stop_reason'] else 'completed' if run['requests_attempted'] == 20 else 'checkpoint_saved' if checkpoint else 'interrupted'
        save()
    return run

if __name__ == '__main__':
    import re
    import msvcrt
    parser = argparse.ArgumentParser(description='Resumable bounded pilot, no automatic retries.')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--checkpoint', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if not args.execute or not re.fullmatch(r'vision_openai_sol_20_[a-zA-Z0-9_-]+', args.run_id):
        parser.error('Explicit --execute and safe unique run ID required.')
    OUTPUT = ROOT / 'evaluation/reports' / args.run_id
    if args.resume:
        if not (OUTPUT / 'raw_results.json').exists(): parser.error('No cache to resume')
    else:
        OUTPUT.mkdir(exist_ok=False)
    logging.disable(logging.CRITICAL)
    # OS-held byte lock prevents concurrent writers; release occurs even on process exit.
    with (OUTPUT / 'execution.lock').open('a+b') as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b'1'); lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            execute(checkpoint=args.checkpoint)
        finally:
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
