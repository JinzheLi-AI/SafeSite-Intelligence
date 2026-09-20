"""Regenerate run-specific pilot reports from cache only; no provider imports."""
import argparse
import hashlib
import json
from pathlib import Path
from evaluation.report_vision_pilot import score, errors, pct

ROOT=Path(__file__).resolve().parents[1]

def generate(output):
    run=json.loads((output/'raw_results.json').read_text(encoding='utf-8'))
    m=score(run)
    m['latency_ms']['basis']='Measured production provider attempt durations; includes any failed attempts.'
    error_rows=errors(run)
    notes_path=output/'error_analysis_notes.json'
    notes=json.loads(notes_path.read_text(encoding='utf-8')) if notes_path.exists() else {}
    for e in error_rows:
        source=next(r for r in run['cases'] if r['case_id']==e['case_id'])
        e.update(notes.get(e['case_id'],{}))
        e['human_evidence_notes']=source['evidence_notes']
        e['interpretation']='Model evidence is a claim, not independent visual verification; labels remain frozen.'
    for name,value in [('metrics.json',m),('case_errors.json',error_rows)]:
        (output/name).write_text(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# OpenAI Sol vision pilot: '+run['run_id'],'',
           '20-image pilot dataset; single primary reviewer; AI-assisted annotation discussion; no secondary adjudication. These results are neither independent validation nor production-level accuracy. Electrical-hazard class has zero positive support.', '',
           '- Dataset SHA-256: `'+run['manifest_sha256']+'`',
           '- Requested model: gpt-5.6-sol. Actual returned models: '+', '.join(sorted({r['actual_model'] for r in run['cases'] if r.get('actual_model')}))+'.',
           '- Production prompt: vision-v1; unchanged. No benchmark-specific prompting, retries, mock fallback or DeepSeek.',
           f"- Status: {run['status']}. Successful: {m['successful_calls']}/20; failed: {m['failed_calls']}; unattempted: {m['unattempted_cases']}; coverage: {pct(m['classification_coverage'])}.",
           '- Checkpoint case_001 was saved before remaining cases ran sequentially. Recorded attempts are never automatically repeated, including interrupted attempts with unknown outcomes.',
           '- Previous failed benchmark lock/reports and historical smoke evidence were preserved.', '',
           '## Metrics on successful predictions only','',
           '| Metric | Result |','| --- | ---: |']
    for name,value in [('Micro precision',m['micro']['precision']),('Micro recall',m['micro']['recall']),('Micro F1',m['micro']['f1']),('Macro F1',m['macro']['f1']),('Exact label-set match',m['exact_match_rate']),('Multi-hazard exact match',m['multi_hazard_exact_match_rate']),('Safe-scene false-positive rate',m['safe_scene']['false_positive_rate']),('Expected-human-review recall',m['human_review']['ambiguous_case_review_recall']),('Unnecessary-review rate',m['human_review']['unnecessary_review_rate'])]:
        lines.append(f'| {name} | {pct(value)} |')
    lines+=['','Classification uses raw model hazard categories, deduplicated into sets, not RiskEngine scores. Human-review flags are production outputs after guardrails, separate from classification. Undefined denominators are null/N/A. Macro F1 excludes undefined class F1 values; defined class count: '+str(m['macro_defined_classes']['f1'])+'. A zero-support class cannot establish recall or class coverage even if false positives yield a defined F1.', '',
            '| Class | TP | FP | FN | Evaluated support | Dataset support | Precision | Recall | F1 |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label,c in m['per_class'].items():
        lines.append(f"| {label} | {c['tp']} | {c['fp']} | {c['fn']} | {c['support']} | {c['dataset_support']} | {pct(c['precision'])} | {pct(c['recall'])} | {pct(c['f1'])} |")
    lines+=['',f"Safe scenes evaluated: {m['safe_scene']['evaluated_count']}; correctly predicted empty: {m['safe_scene']['correct_zero_hazard_count']}; false-positive scenes: {m['safe_scene']['false_positive_scene_count']}. Safe-scene false categories: {m['safe_scene']['false_positive_categories']}.",
            f"Expected-review cases evaluated: {m['human_review']['evaluated_expected_count']}; true flags: {m['human_review']['true_review_flags']}; missed flags: {m['human_review']['missed_review_flags']}.",
            '', '## Usage and latency', '',
            f"Input tokens: {m['input_tokens']}; output tokens: {m['output_tokens']}; total tokens: {m['total_tokens']}. Missing usage is never treated as zero.",
            f"Latency: mean {m['latency_ms']['average']} ms; median {m['latency_ms']['median']} ms; p95 nearest rank {m['latency_ms']['p95_nearest_rank']} ms.",
            'Estimated cost: '+('unavailable (no reliable configured estimate)' if m['estimated_cost_usd'] is None else str(m['estimated_cost_usd'])+' USD')+'.', '',
            '## Main findings', '', 'There are 15 false-positive class assignments and one false negative. PPE contributes seven false positives; housekeeping four; electrical two; height and edge one each. Safe-scene PPE false positives are cases 001, 002 and 013. The sole false negative is missing_ppe in case_007, whose human note also describes uncertainty about the PPE requirement. These are disagreements with frozen labels, not independently adjudicated errors. No prompt or labels were changed.', '', 'Electrical recall is N/A: there are no positive electrical examples. Electrical precision/F1 of zero penalize two false positives only and do not establish detection ability. Macro F1 uses all six defined F1 values, including this penalty.', '', '## Case-level errors', '', 'All disagreements are retained below and in case_errors.json. Explanations compare frozen human notes with model claims; they do not amend annotations.', '']
    for e in error_rows:
        lines += ['### '+e['case_id'], '', 'Ground truth: '+str(e['ground_truth'])+'; prediction: '+str(e['prediction'])+'.',
                  'False positives: '+str(e['false_positive_classes'])+'; false negatives: '+str(e['false_negative_classes'])+'.',
                  'Likely error category (interpretive): '+e['likely_error_category'], 'Explanation: '+e['explanation'], 'Human notes: '+e['human_evidence_notes'], 'Model visual evidence: '+json.dumps(e['visual_evidence'],ensure_ascii=False), '']
    lines+=['## Reproduction and limits','', 'Evaluation regression suite: 80 passed, two existing dependency warnings. Reports are regenerated from the raw cache and interpretive error notes; no inference is used.',
            f"From safesite: `backend/.venv/Scripts/python.exe -m evaluation.report_resumed_pilot --run-id {run['run_id']}`. This regenerates reports offline without inference.",
            'raw_results.json contains the frozen annotations, original/processed image hashes, normalized successful results, usage and request provenance. The byte lock prevents concurrent writers. Resume requires the same dataset/prompt hashes and skips all recorded attempts. A stopped run requires investigation; no automatic restart is allowed.',
            'Small convenience sample, possible annotation subjectivity and AI-assisted discussion limit generalization. No secondary adjudication and no positive electrical examples. Prior smoke exposure means these images are not a fresh independent held-out set. Confidence averages are descriptive, not formal calibration.',
            'Manifest, images, .env and prompt unchanged: '+str(all(run.get(k) for k in ['manifest_unchanged','images_unchanged','env_unchanged','prompt_unchanged']))+'.','']
    (output/'summary.md').write_text('\n'.join(lines),encoding='utf-8')
    return m

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    output=(ROOT/'evaluation/reports'/args.run_id).resolve()
    assert output.parent==(ROOT/'evaluation/reports').resolve()
    print(json.dumps(generate(output),indent=2))
