"""Offline pilot-manifest validation. No model, product settings or inference imports."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

IMAGE_ROOT = Path(__file__).resolve().parent
HAZARDS = {'missing_ppe', 'working_at_height', 'unprotected_edge', 'unsafe_scaffolding', 'electrical_hazard', 'housekeeping'}
GROUPS = {'safe', 'ppe', 'working_at_height', 'unprotected_edge', 'unsafe_scaffolding', 'electrical', 'housekeeping', 'multi_hazard', 'ambiguous'}
STATUSES = {'missing_image', 'unreviewed', 'reviewed', 'adjudicated'}
FIELDS = {'case_id', 'image_path', 'image_hash', 'ground_truth_hazards', 'ambiguous', 'expected_human_review', 'evidence_notes', 'reviewer', 'secondary_reviewer', 'label_status', 'source', 'license_or_provenance', 'group'}


def filled(value):
    return isinstance(value, str) and bool(value.strip())


def validate_dataset(path, image_root=IMAGE_ROOT):
    result = {'total_cases': 0, 'images_present': 0, 'missing_images': 0, 'reviewed': 0,
              'adjudicated': 0, 'benchmark_ready': 0, 'duplicate_images': 0,
              'errors': [], 'warnings': [], 'ready_case_ids': []}
    try:
        rows = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        result['errors'].append('Cannot read manifest: ' + type(exc).__name__)
        return result
    if not isinstance(rows, list):
        result['errors'].append('Manifest must be a JSON array.')
        return result
    result['total_cases'] = len(rows)
    if len(rows) != 20:
        result['errors'].append('Exactly 20 cases are required.')
    counts = Counter(r.get('case_id') for r in rows if isinstance(r, dict) and isinstance(r.get('case_id'), str))
    expected = {f'case_{n:03d}' for n in range(1, 21)}
    if set(counts) != expected:
        result['errors'].append('Case IDs must be exactly case_001 through case_020.')
    by_hash = defaultdict(list)
    ready = {}
    root = Path(image_root).resolve()
    for index, row in enumerate(rows):
        prefix = f'Row {index + 1}'
        if not isinstance(row, dict):
            result['errors'].append(prefix + ': expected an object.')
            continue
        local = []
        case_id = row.get('case_id')
        if isinstance(case_id, str):
            prefix += ' (' + case_id + ')'
        if not isinstance(case_id, str) or case_id not in expected:
            local.append('invalid case_id')
        elif counts[case_id] != 1:
            local.append('duplicate case_id')
        for name in sorted(FIELDS - row.keys()):
            local.append('missing field: ' + name)
        for name in sorted(row.keys() - FIELDS):
            local.append('unknown field: ' + name)
        status = row.get('label_status')
        if not isinstance(status, str) or status not in STATUSES:
            local.append('invalid label_status')
        if status == 'reviewed': result['reviewed'] += 1
        if status == 'adjudicated': result['adjudicated'] += 1
        for name in ['image_path', 'image_hash', 'evidence_notes', 'reviewer', 'secondary_reviewer', 'source', 'license_or_provenance', 'group']:
            if row.get(name) is not None and not isinstance(row[name], str):
                local.append(name + ' must be a string or null')
        group = row.get('group')
        if group not in (None, '') and (not isinstance(group, str) or group not in GROUPS):
            local.append('invalid intended group')
        hazards = row.get('ground_truth_hazards')
        if hazards is not None:
            if not isinstance(hazards, list) or any(not isinstance(h, str) or h not in HAZARDS for h in hazards):
                local.append('ground_truth_hazards must be a list of supported labels or null')
            elif len(set(hazards)) != len(hazards):
                local.append('duplicate hazard labels')
        for name in ['ambiguous', 'expected_human_review']:
            if row.get(name) is not None and type(row[name]) is not bool:
                local.append(name + ' must be a boolean or null')
        if status in ('reviewed', 'adjudicated'):
            for name in ['reviewer', 'evidence_notes']:
                if not filled(row.get(name)): local.append(name + ' is required for a human-reviewed case')
            if hazards is None: local.append('ground_truth_hazards is required; [] is valid for a reviewed negative')
            for name in ['ambiguous', 'expected_human_review']:
                if type(row.get(name)) is not bool: local.append(name + ' is required')
            if not filled(row.get('source')) or not filled(row.get('license_or_provenance')):
                result['warnings'].append(prefix + ': source/provenance incomplete; supply it where available.')
            if row.get('ambiguous') is True and row.get('expected_human_review') is False:
                result['warnings'].append(prefix + ': ambiguous case normally expects human review; explain the exception in evidence_notes.')
        path_value, claimed_hash = row.get('image_path'), row.get('image_hash')
        if status == 'missing_image':
            result['missing_images'] += 1
            if path_value not in (None, '') or claimed_hash not in (None, ''):
                local.append('missing_image requires empty image_path and image_hash')
            for name in ['ground_truth_hazards', 'ambiguous', 'expected_human_review', 'evidence_notes', 'reviewer', 'secondary_reviewer']:
                if row.get(name) not in (None, ''):
                    local.append('missing_image cannot contain human labels: ' + name)
        else:
            try:
                if not filled(path_value): raise ValueError('image_path is required')
                if Path(path_value).is_absolute(): raise ValueError('image_path must be relative to image root')
                image = (root / path_value).resolve()
                if not image.is_relative_to(root): raise ValueError('image_path escapes image root')
                if not image.is_file(): raise ValueError('referenced image does not exist')
                actual_hash = hashlib.sha256(image.read_bytes()).hexdigest()
                result['images_present'] += 1
                by_hash[actual_hash].append(index)
                if not isinstance(claimed_hash, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', claimed_hash):
                    local.append('image_hash must contain the actual SHA-256 digest')
                elif actual_hash != claimed_hash.lower(): local.append('image hash mismatch')
            except (OSError, ValueError) as exc:
                local.append(str(exc))
                result['missing_images'] += 1
        result['errors'].extend(prefix + ': ' + message for message in local)
        if status in ('reviewed', 'adjudicated') and not local:
            ready[index] = case_id
    for digest, indices in by_hash.items():
        if len(indices) > 1:
            result['duplicate_images'] += len(indices) - 1
            names = [str(rows[i].get('case_id')) for i in indices]
            result['errors'].append('Duplicate image hash ' + digest + ': ' + ', '.join(names))
            for index in indices: ready.pop(index, None)
    result['ready_case_ids'] = list(ready.values())
    result['benchmark_ready'] = len(ready)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--image-root', type=Path, default=IMAGE_ROOT,
                        help='Image paths are relative to this directory; default: evaluation/.')
    parser.add_argument('--json', action='store_true', help='Print the complete machine-readable result.')
    args = parser.parse_args()
    result = validate_dataset(args.manifest, args.image_root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for label, name in [('Total cases', 'total_cases'), ('Images present', 'images_present'),
                            ('Missing images', 'missing_images'), ('Reviewed', 'reviewed'),
                            ('Adjudicated', 'adjudicated'), ('Benchmark-ready', 'benchmark_ready'),
                            ('Duplicate images', 'duplicate_images')]:
            print(f'{label}: {result[name]}')
        print(f"Validation errors: {len(result['errors'])}")
        for error in result['errors']: print('ERROR: ' + error)
        for warning in result['warnings']: print('WARNING: ' + warning)
        print('Validation never runs inference. Incomplete slots are allowed; a passing check does not mean all 20 images are ready.')
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
