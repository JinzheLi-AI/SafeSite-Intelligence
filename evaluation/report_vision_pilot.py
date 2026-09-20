"""Offline pilot scoring and reporting. No provider imports or network operations."""
import json
import math
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'evaluation/reports/vision_openai_sol_20'
CLASSES = ['missing_ppe', 'working_at_height', 'unprotected_edge', 'unsafe_scaffolding', 'electrical_hazard', 'housekeeping']

def divide(a, b):
    return a / b if b else None

def average(values):
    return mean(values) if values else None

def scores(tp, fp, fn):
    return dict(precision=divide(tp, tp + fp), recall=divide(tp, tp + fn), f1=divide(2 * tp, 2 * tp + fp + fn))

def score(run):
    if any('class_decisions' in r for r in run['manifest_snapshot']):
        raise ValueError('Use vision-three-state-v1 scoring for V2 manifests; legacy scoring is binary only')
    rows = run['cases']
    good = [r for r in rows if r['provider_success']]
    attempted = [r for r in rows if r.get('requests_attempted', 0)]
    classes = {}
    for label in CLASSES:
        tp = sum(label in r['ground_truth_hazards'] and label in r['predicted_hazards'] for r in good)
        fp = sum(label not in r['ground_truth_hazards'] and label in r['predicted_hazards'] for r in good)
        fn = sum(label in r['ground_truth_hazards'] and label not in r['predicted_hazards'] for r in good)
        classes[label] = dict(tp=tp if good else None, fp=fp if good else None, fn=fn if good else None,
                              support=sum(label in r['ground_truth_hazards'] for r in good),
                              dataset_support=sum(label in r['ground_truth_hazards'] for r in run['manifest_snapshot']),
                              **scores(tp, fp, fn))
    totals = {k: sum(c[k] or 0 for c in classes.values()) for k in ['tp', 'fp', 'fn']}
    safe = [r for r in good if not r['ground_truth_hazards']]
    multi = [r for r in good if len(r['ground_truth_hazards']) > 1]
    expected = [r for r in good if r['expected_human_review']]
    unexpected = [r for r in good if not r['expected_human_review']]
    ambiguous = [r for r in good if r['ambiguous']]
    confidence = {kind: [h['confidence'] for r in good for h in r['hazard_confidences']
                         if (h['hazard_type'] in r['ground_truth_hazards']) == (kind == 'true_positive')] for kind in ['true_positive', 'false_positive']}
    latency = sorted(r['latency_ms'] for r in attempted if r.get('latency_ms') is not None)
    metrics = dict(status=run['status'], planned_cases=len(run['manifest_snapshot']), successful_calls=len(good),
                   failed_calls=len(attempted) - len(good), unattempted_cases=len(rows) - len(attempted),
                   classification_coverage=divide(len(good), len(rows)),
                   micro=scores(**totals),
                   macro={k: average([c[k] for c in classes.values() if c[k] is not None]) for k in ['precision', 'recall', 'f1']},
                   macro_defined_classes={k: sum(c[k] is not None for c in classes.values()) for k in ['precision', 'recall', 'f1']},
                   per_class=classes, false_positive_count=totals['fp'] if good else None,
                   false_negative_count=totals['fn'] if good else None,
                   exact_match_rate=divide(sum(set(r['ground_truth_hazards']) == set(r['predicted_hazards']) for r in good), len(good)),
                   multi_hazard_cases=len(multi), multi_hazard_exact_match_rate=divide(sum(set(r['ground_truth_hazards']) == set(r['predicted_hazards']) for r in multi), len(multi)),
                   safe_scene=dict(dataset_count=sum(not r['ground_truth_hazards'] for r in run['manifest_snapshot']), evaluated_count=len(safe),
                                   correct_zero_hazard_count=sum(not r['predicted_hazards'] for r in safe),
                                   false_positive_scene_count=sum(bool(r['predicted_hazards']) for r in safe),
                                   false_positive_label_count=sum(len(r['predicted_hazards']) for r in safe),
                                   false_positive_rate=divide(sum(bool(r['predicted_hazards']) for r in safe), len(safe)),
                                   false_positive_categories=sorted({h for r in safe for h in r['predicted_hazards']})),
                   human_review=dict(dataset_expected_count=sum(r['expected_human_review'] for r in run['manifest_snapshot']),
                                     evaluated_expected_count=len(expected), true_review_flags=sum(r['requires_human_review'] for r in expected),
                                     missed_review_flags=sum(not r['requires_human_review'] for r in expected),
                                     ambiguous_case_review_recall=divide(sum(r['requires_human_review'] for r in expected), len(expected)),
                                     ambiguous_subset_count=len(ambiguous), ambiguous_subset_review_recall=divide(sum(r['requires_human_review'] for r in ambiguous), len(ambiguous)),
                                     unnecessary_review_rate=divide(sum(r['requires_human_review'] for r in unexpected), len(unexpected))),
                   confidence={k: dict(count=len(v), mean=average(v)) for k, v in confidence.items()},
                   latency_ms=dict(count=len(latency), average=average(latency), median=median(latency) if latency else None,
                                   p95_nearest_rank=latency[math.ceil(.95 * len(latency)) - 1] if latency else None,
                                   basis='Local provider-attempt duration including failed connections; not successful inference latency.'),
                   methodology='Classification uses successful structured outputs only; failures are unavailable, never negative predictions. Undefined ratios are null; macro averages exclude undefined class ratios and expose denominators. Human review uses production post-guardrail flag. No RiskEngine classification input.')
    for key in ['input_tokens', 'output_tokens', 'total_tokens', 'estimated_cost_usd']:
        values = [r.get(key) for r in attempted]
        metrics[key] = sum(values) if values and all(v is not None for v in values) else None
        metrics[key + '_reported_calls'] = sum(v is not None for v in values)
    metrics['average_tokens_per_attempted_image'] = divide(metrics['total_tokens'], len(attempted)) if metrics['total_tokens'] is not None else None
    return metrics

def errors(run):
    if any("class_decisions" in r for r in run["manifest_snapshot"]):
        raise ValueError("Use vision-three-state-v1 error attribution for V2 manifests")
    output = []
    for r in run['cases']:
        base = dict(case_id=r['case_id'], ground_truth=r['ground_truth_hazards'], prediction=r.get('predicted_hazards'), visual_evidence=r.get('visual_evidence'))
        if not r['provider_success']:
            output.append(dict(base, false_positive_classes=None, false_negative_classes=None,
                               likely_error_category='provider_connection_failure' if r.get('requests_attempted') else 'not_attempted_after_stop',
                               explanation='No model prediction exists; cannot attribute a visual recognition error.', provider_error=r['provider_error']))
            continue
        fp = sorted(set(r['predicted_hazards']) - set(r['ground_truth_hazards']))
        fn = sorted(set(r['ground_truth_hazards']) - set(r['predicted_hazards']))
        if fp or fn:
            output.append(dict(base, false_positive_classes=fp, false_negative_classes=fn,
                               likely_error_category='requires_case_level_evidence_review',
                               explanation='Label-set disagreement with frozen primary reviewer; causal attribution requires evidence review.'))
    return output

def pct(value):
    return 'Unavailable' if value is None else f'{value:.2%}'

def render(run, m, case_errors):
    lines = ['# OpenAI Sol: 20-image manually reviewed pilot benchmark', '',
             '**Status: stopped after four connection failures; no successful image inference.**', '',
             'Ground truth was supplied by one primary human reviewer; no secondary adjudication was performed. This is not production accuracy, independent large-scale validation, or a statistically definitive benchmark.', '',
             '## Preflight and execution', '',
             '- 20/20 reviewed images passed manifest validation, SHA-256 verification and unchanged production preprocessing; zero duplicates.',
             '- Requested provider/model: openai / gpt-5.6-sol. Actual returned model: unavailable (no API response). Prompt: vision-v1, unchanged.',
             f"- Planned requests: 20. Attempted: {run['requests_attempted']}. Successful: {m['successful_calls']}. Failed: {m['failed_calls']}. Not attempted: {m['unattempted_cases']}.",
             '- case_001 through case_004 failed with connection_error. No HTTP status, response ID, model output or usage was received. Whether any attempt was billable cannot be determined.',
             '- The runner stopped at more than three provider failures. No automatic retries, mock substitutions, DeepSeek calls or second paid pass occurred.',
             '- Processed bytes were verified in each outgoing request before transport. Delivery to OpenAI could not be confirmed. Credentials, billing and model access remain unconfirmed by this run.',
             '- The exact network cause was not established. A connection failure is not evidence of invalid credentials, exhausted billing, or an unavailable model.', '',
             '## Competition-ready table', '',
             '| Capability | Metric | Result |', '| --- | --- | --- |']
    for capability, metric, value in [
        ('Hazard Recognition (20-image pilot)', 'Micro Precision', pct(m['micro']['precision'])),
        ('Hazard Recognition (20-image pilot)', 'Micro Recall', pct(m['micro']['recall'])),
        ('Hazard Recognition (20-image pilot)', 'Micro F1', pct(m['micro']['f1'])),
        ('Hazard Recognition (20-image pilot)', 'Macro F1', pct(m['macro']['f1'])),
        ('Exact Match (20-image pilot)', 'Label-set exact match', pct(m['exact_match_rate'])),
        ('Safe Scene (20-image pilot)', 'False-positive rate', pct(m['safe_scene']['false_positive_rate'])),
        ('Human Review (20-image pilot)', 'Ambiguous-case review recall', pct(m['human_review']['ambiguous_case_review_recall'])),
        ('Human Review (20-image pilot)', 'Unnecessary-review rate', pct(m['human_review']['unnecessary_review_rate'])),
        ('Regulation Retrieval (prior measurement)', 'Recall@3', '88.89%'),
        ('Regulation Safety (prior measurement)', 'Unsupported citations', '0/100'),
        ('Risk Policy (prior deterministic test)', 'Correctness', '40/40'),
        ('Workflow (prior injected-AI tests)', 'Scenario success', '20/20')]:
        lines.append(f'| {capability} | {metric} | {value} |')
    lines += ['', 'Prior retrieval/policy/workflow figures are preserved historical evidence, not rerun here. Vision metrics are unavailable, not zero. No successful prediction exists to count a false positive or false negative.', '',
              '## Per-class results', '', '| Class | Dataset support | Evaluated support | F1 |', '| --- | ---: | ---: | --- |']
    for label, c in m['per_class'].items():
        lines.append(f"| {label} | {c['dataset_support']} | {c['support']} | {pct(c['f1'])} |")
    lines += ['', f"Safe scenes in reviewed dataset: {m['safe_scene']['dataset_count']}; evaluated safe scenes: 0. Expected-review cases: {m['human_review']['dataset_expected_count']}; evaluated expected-review cases: 0.",
              'Micro/macro precision and recall, multi-hazard exact match, confidence comparisons, main FP/FN categories and PPE false-positive recurrence are all unavailable. No calibration claim is possible.', '',
              '## Tokens, latency and cost', '',
              '- Input/output/total tokens: unavailable; 0/4 attempts supplied usage. This does not establish zero token consumption.',
              '- Estimated cost: unavailable. No response usage or billable outcome was established; no pricing was invented.',
              f"- Local failed-attempt latency: mean {m['latency_ms']['average']} ms; median {m['latency_ms']['median']} ms; p95 (nearest rank) {m['latency_ms']['p95_nearest_rank']} ms. These are not successful inference latencies.", '',
              '## Error analysis and next steps', '',
              'case_errors.json retains all four provider failures and all sixteen unattempted cases. Visual error taxonomy cannot be assigned without predictions; no ground truth was altered.',
              '1. Diagnose and restore execution-environment connectivity to the official OpenAI endpoint; do not infer a credential or billing problem from connection_error.',
              '2. Obtain authorization for a separate future run after connectivity is restored. Preserve this failed run and its one-shot lock; do not resume or overwrite it automatically.',
              '3. Once valid predictions exist, assess PPE requirement inference and other visual failures against frozen labels; add independent secondary review before stronger claims.',
              'No evidence supports changing the production prompt from this run. The results are insufficient for a measured competition vision-accuracy claim.', '',
              '## Reproduction and integrity', '', 'Affected evaluation/provider/preprocessing tests: 147 passed, with two existing dependency deprecation warnings. Generated JSON validated and offline report regeneration was byte-identical; no extra API calls.', '',
              'Regenerate reports offline from safesite: `backend/.venv/Scripts/python.exe evaluation/report_vision_pilot.py`. This command has no provider imports or API calls.',
              'Classification scoring uses model categories before RiskEngine, deduplicated by class. Undefined ratios remain null; macro means exclude undefined ratios with denominators recorded. Failed requests are never scored as empty labels. Human-review metrics use the production flag after guardrails and remain separate from classification.',
              f"Manifest unchanged: {run['manifest_unchanged']}; images unchanged: {run['images_unchanged']}; prompt unchanged: {run['prompt_unchanged']}; .env unchanged: {run['env_unchanged']}.",
              'raw_results.json contains the frozen manifest, request hashes, all attempt accounting and explicit unattempted records. Successful normalized outputs would be cached there; none exist in this run.', '']
    return '\n'.join(lines)

def generate():
    run = json.loads((OUTPUT / 'raw_results.json').read_text(encoding='utf-8'))
    m, e = score(run), errors(run)
    for name, data in [('metrics.json', m), ('case_errors.json', e)]:
        (OUTPUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=True, allow_nan=False) + '\n', encoding='utf-8')
    summary = render(run, m, e)
    (OUTPUT / 'summary.md').write_text(summary, encoding='utf-8')
    return m

if __name__ == '__main__':
    print(json.dumps(generate(), indent=2))
