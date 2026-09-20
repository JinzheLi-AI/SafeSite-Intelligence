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

def execute():
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
    # Permanent guard: interruption never authorizes reissuing a possibly billed request.
    with (OUTPUT / 'execution.lock').open('x', encoding='utf-8') as stream:
        stream.write(datetime.now(timezone.utc).isoformat())
    run = dict(schema_version='vision-pilot-single-pass-v1', started_at=datetime.now(timezone.utc).isoformat(),
               manifest_sha256=digest(frozen), prompt_file_sha256=prompt_hash, manifest_snapshot=cases,
               provider='openai', requested_model='gpt-5.6-sol', prompt_version='vision-v1',
               planned_requests=20, maximum_requests=20, requests_attempted=0, sdk_retries=0, validation_attempts=1,
               preflight=validation, billing_precheck='No separate billing endpoint available; first authorized inference gates access.',
               status='running', stop_reason=None, cases=[])
    def save():
        write_json(OUTPUT / 'raw_results.json', run)
    save()
    failures = 0
    try:
        for case in cases:
            if run['stop_reason']:
                run['cases'].append(dict(case, provider='openai', requested_model='gpt-5.6-sol', prompt_version='vision-v1',
                                         provider_success=False, provider_error='not_attempted_after_stop', requests_attempted=0))
                save()
                continue
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
                row.update(provider_success=True, normalized_result=answer.model_dump(mode='json'), raw_visual_output=raw,
                           predicted_hazards=sorted({h['hazard_type'] for h in raw['hazards']}),
                           hazard_confidences=[dict(hazard_type=h['hazard_type'], confidence=h['confidence']) for h in raw['hazards']],
                           overall_confidence=answer.overall_confidence, requires_human_review=answer.requires_human_review,
                           model_requires_human_review=raw['requires_human_review'],
                           visual_evidence=[dict(hazard_type=h['hazard_type'], evidence=h['visual_evidence'], description=h['description']) for h in raw['hazards']])
            except Exception as exc:
                code = getattr(exc, 'code', type(exc).__name__)
                row['provider_error'] = code
                failures += 1
                if code in {'invalid_credentials', 'missing_credentials', 'model_unavailable', 'rate_limited', 'invalid_provider_request'}:
                    run['stop_reason'] = code
                elif code == 'invalid_output' and any(r.get('provider_error') == 'invalid_output' for r in run['cases'][:-1]):
                    run['stop_reason'] = 'systematic_schema_failure'
                elif failures > 3:
                    run['stop_reason'] = 'more_than_three_provider_failures'
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
        run['completed_at'] = datetime.now(timezone.utc).isoformat()
        run['status'] = 'stopped' if run['stop_reason'] else 'completed' if len(run['cases']) == 20 else 'interrupted'
        save()
    return run

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    if not args.execute:
        parser.error('Requires --execute. Reports are regenerated with report_vision_pilot.py, never this runner.')
    try:
        execute()
    except Exception as exc:
        print('Stopped safely: ' + type(exc).__name__ + '. No automatic retry.', flush=True)
        sys.exit(1)

