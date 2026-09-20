# OpenAI Sol: 20-image manually reviewed pilot benchmark

**Status: stopped after four connection failures; no successful image inference.**

Ground truth was supplied by one primary human reviewer; no secondary adjudication was performed. This is not production accuracy, independent large-scale validation, or a statistically definitive benchmark.

## Preflight and execution

- 20/20 reviewed images passed manifest validation, SHA-256 verification and unchanged production preprocessing; zero duplicates.
- Requested provider/model: openai / gpt-5.6-sol. Actual returned model: unavailable (no API response). Prompt: vision-v1, unchanged.
- Planned requests: 20. Attempted: 4. Successful: 0. Failed: 4. Not attempted: 16.
- case_001 through case_004 failed with connection_error. No HTTP status, response ID, model output or usage was received. Whether any attempt was billable cannot be determined.
- The runner stopped at more than three provider failures. No automatic retries, mock substitutions, DeepSeek calls or second paid pass occurred.
- Processed bytes were verified in each outgoing request before transport. Delivery to OpenAI could not be confirmed. Credentials, billing and model access remain unconfirmed by this run.
- The exact network cause was not established. A connection failure is not evidence of invalid credentials, exhausted billing, or an unavailable model.

## Competition-ready table

| Capability | Metric | Result |
| --- | --- | --- |
| Hazard Recognition (20-image pilot) | Micro Precision | Unavailable |
| Hazard Recognition (20-image pilot) | Micro Recall | Unavailable |
| Hazard Recognition (20-image pilot) | Micro F1 | Unavailable |
| Hazard Recognition (20-image pilot) | Macro F1 | Unavailable |
| Exact Match (20-image pilot) | Label-set exact match | Unavailable |
| Safe Scene (20-image pilot) | False-positive rate | Unavailable |
| Human Review (20-image pilot) | Ambiguous-case review recall | Unavailable |
| Human Review (20-image pilot) | Unnecessary-review rate | Unavailable |
| Regulation Retrieval (prior measurement) | Recall@3 | 88.89% |
| Regulation Safety (prior measurement) | Unsupported citations | 0/100 |
| Risk Policy (prior deterministic test) | Correctness | 40/40 |
| Workflow (prior injected-AI tests) | Scenario success | 20/20 |

Prior retrieval/policy/workflow figures are preserved historical evidence, not rerun here. Vision metrics are unavailable, not zero. No successful prediction exists to count a false positive or false negative.

## Per-class results

| Class | Dataset support | Evaluated support | F1 |
| --- | ---: | ---: | --- |
| missing_ppe | 3 | 0 | Unavailable |
| working_at_height | 8 | 0 | Unavailable |
| unprotected_edge | 1 | 0 | Unavailable |
| unsafe_scaffolding | 1 | 0 | Unavailable |
| electrical_hazard | 0 | 0 | Unavailable |
| housekeeping | 2 | 0 | Unavailable |

Safe scenes in reviewed dataset: 7; evaluated safe scenes: 0. Expected-review cases: 8; evaluated expected-review cases: 0.
Micro/macro precision and recall, multi-hazard exact match, confidence comparisons, main FP/FN categories and PPE false-positive recurrence are all unavailable. No calibration claim is possible.

## Tokens, latency and cost

- Input/output/total tokens: unavailable; 0/4 attempts supplied usage. This does not establish zero token consumption.
- Estimated cost: unavailable. No response usage or billable outcome was established; no pricing was invented.
- Local failed-attempt latency: mean 471.25 ms; median 37.5 ms; p95 (nearest rank) 1790 ms. These are not successful inference latencies.

## Error analysis and next steps

case_errors.json retains all four provider failures and all sixteen unattempted cases. Visual error taxonomy cannot be assigned without predictions; no ground truth was altered.
1. Diagnose and restore execution-environment connectivity to the official OpenAI endpoint; do not infer a credential or billing problem from connection_error.
2. Obtain authorization for a separate future run after connectivity is restored. Preserve this failed run and its one-shot lock; do not resume or overwrite it automatically.
3. Once valid predictions exist, assess PPE requirement inference and other visual failures against frozen labels; add independent secondary review before stronger claims.
No evidence supports changing the production prompt from this run. The results are insufficient for a measured competition vision-accuracy claim.

## Reproduction and integrity

Affected evaluation/provider/preprocessing tests: 147 passed, with two existing dependency deprecation warnings. Generated JSON validated and offline report regeneration was byte-identical; no extra API calls.

Regenerate reports offline from safesite: `backend/.venv/Scripts/python.exe evaluation/report_vision_pilot.py`. This command has no provider imports or API calls.
Classification scoring uses model categories before RiskEngine, deduplicated by class. Undefined ratios remain null; macro means exclude undefined ratios with denominators recorded. Failed requests are never scored as empty labels. Human-review metrics use the production flag after guardrails and remain separate from classification.
Manifest unchanged: True; images unchanged: True; prompt unchanged: True; .env unchanged: True.
raw_results.json contains the frozen manifest, request hashes, all attempt accounting and explicit unattempted records. Successful normalized outputs would be cached there; none exist in this run.

---

# Historical dataset-gate report (superseded by the run above)

# OpenAI Sol formal vision benchmark ? dataset gate

Audit date: 2026-09-17. **NOT RUN: insufficient human-reviewed data.** This is an offline dataset audit, not a formal benchmark or a scored pilot evaluation. No accuracy claim is supported.

## Audited dataset

Inspected evaluation/datasets, evaluation/fixtures and equivalent evaluation records. evaluation/manifests does not exist. hazards.json contains 72 placeholder slots, all with no reviewed labels. The artificial hazard_scoring.json fixture tests metric arithmetic; it is not a real image benchmark. Smoke-response files contain model predictions and cannot supply ground truth.

Four distinct JPEG files exist:

| File | Original dimensions | Provider dimensions | Label status |
| --- | --- | --- | --- |
| fixtures/live_smoke/01_safe.jpg | 5118 x 7677 | 1600 x 2400 | Unlabeled |
| fixtures/live_smoke/02_obvious_hazard.jpg | 5614 x 3733 | 5614 x 3733 | Unlabeled |
| fixtures/live_smoke/03_ambiguous.jpg | 5184 x 3888 | 5184 x 3888 | Unlabeled |
| fixtures/live_smoke/04_multi_hazard.jpg | 4924 x 3283 | 4924 x 3283 | Unlabeled |

All four exist, verify as JPEG and fully decode/process through the existing image helper. Originals were read only. Four distinct hashes establish byte-level uniqueness, not independent scenes or verified provenance. Image ownership, licensing and independent reviewer judgments are not established by their presence on disk.

**Reviewed real images: 0. Unlabeled files: 4. Placeholder slots: 72.** Reviewed safe/ambiguous/multi-hazard cases: 0 each; actual counts in those categories are unknown. No truth was inferred from filenames, captions, previous AI predictions or recruitment-slot descriptions.

Manifest SHA-256: fb47e6cab76aac1da319511d5b3931759184608bce94a5ef910e9f2e16ac9703. Per-image original and processed hashes, byte counts and dimensions are in [the audit JSON](../evaluation/reports/openai_sol_dataset_audit.json). The source manifest was not edited.

## Required human input

Supply at least **20 reviewed real images** for a formal run, preferably **30?50**. If all four current files are suitable, label them and add at least **16** additional real photographs; add **26?46** for the preferred size. If some are unsuitable or lack rights, replace them. Fewer than 20 reviewed images may support only a separately scoped pilot, never a formal benchmark claim. No synthetic images should be added to inflate N.

For every image provide:

- A unique case_id and existing image_path relative to a declared image root.
- Human ground_truth_hazards using only missing_ppe, working_at_height, unprotected_edge, unsafe_scaffolding, electrical_hazard and housekeeping. Use [] only for a reviewed negative; null means unlabeled.
- Human ambiguous and expected_human_review booleans, assessed separately from class correctness.
- Reviewer notes explaining visible evidence, uncertainty and any required PPE/task relationship; not seeing eyewear alone does not prove a violation.
- label_status=reviewed only after review and adjudication.
- Source/license or permission information, and same-site/session grouping to identify leakage or near duplicates.

The existing repository schema additionally requires description, image_sha256, group_id, two distinct reviewer identifiers in reviewers, and license_or_consent for a reviewed row. Its field for reviewer rationale is **notes**, not reviewer_notes. Supply reviewer notes under notes for direct compatibility, or identify reviewer_notes explicitly for a documented import mapping later. These stricter existing requirements were not weakened. Do not copy illustrative hashes, names or labels into real reviewed rows.

Use [LABELING.md](../evaluation/datasets/LABELING.md) for the independent-review process: two humans annotate without seeing model predictions; adjudicate disagreements and retain their original annotations plus the resolution. The first two images have already exposed model predictions in this conversation, so fresh held-out images and reviewers blinded to predictions are preferable. Record any unavoidable prior exposure.

Include genuine safe negatives, ambiguous views, multi-hazard cases and positive support for all six classes. The current task specifies no per-class quota; report actual support and unsupported classes rather than manufacture balance. Keep site/session groups together when splitting data, and freeze the reviewed manifest before inference. Clearly separate visual ambiguity from operational rules that require human confirmation even for obvious hazards.

## Preflight and execution status

Target configuration is openai / gpt-5.6-sol with current production prompt vision-v1. Credential presence was verified without printing its value. Billing availability was not checked remotely; successful earlier smoke calls do not prove current billing availability. The reviewed-dataset gate failed first, so there was no reason to send a paid authentication or inference request.

Validated images: 4/4. Reviewed label candidates: 0. Missing files among real candidates: 0. The 72 placeholders have no assigned files and are not counted as missing benchmark observations. Expected eligible inference calls now: **0**. After supplying N accepted reviewed images, the authorized design is **N SafeSite calls**, one per case, with no additional generic baseline or hidden retry.

The existing evaluation/run.py vision runner is a paired generic/SafeSite baseline runner, so it must **not** be invoked unchanged for this task's one-call-per-image requirement. No tooling was altered before the dataset gate passed. When the reviewed set is available, a bounded SafeSite-only execution path must preserve the production prompt, set one attempt, freeze input hashes and cache normalized/raw results plus per-call accounting. Failed requests must remain in the frozen denominator and be reported separately; report successful-response-only metrics separately if useful, without hiding exclusions.

## Requested metrics and error analyses

All vision metric values below are **N/A (not run)**:

- Micro precision, recall and F1; macro F1.
- Per-class precision/recall/F1/support for each of the six categories.
- False-positive and false-negative counts; safe-scene false-positive rate.
- Multi-hazard exact-match rate; ambiguous-case review recall; obvious-case unnecessary-review rate.
- Correct/incorrect prediction confidence summaries. No meaningful labeled sample exists and no calibration claim is made.

Safe-scene analysis, ambiguous-case analysis and case-level FP/FN enumeration are blocked by missing labels. Earlier smoke output suggested possible eye-protection over-inference, but this is not an adjudicated benchmark error. Do not invent error counts or apply the requested failure taxonomy to unlabeled images. Future errors should be listed per case with ground truth, prediction, evidence and a human assessment of the likely cause, including PPE requirement/occlusion, height/edge ambiguity, scaffolding geometry, electrical ambiguity, housekeeping judgment, duplicates and missed multiple hazards when actually observed.

API calls this task: **0**. Provider failures: **0 attempted-call failures; provider reliability unmeasured** (machine audit uses null for an unrun failure metric). New consumed tokens: none because no calls were made; usage, mean/median latency, per-image cost and total estimated cost remain null/unavailable in the unrun benchmark record. No pricing was invented. Earlier smoke tokens and costs are not pooled into this benchmark. There are no benchmark response caches because nothing was executed.

## Competition summary

These prior non-vision figures were read from the existing saved 2026-09-15 summary, not remeasured. Their provenance and limitations must accompany any competition presentation.

| Capability | Metric | Result |
| --- | --- | --- |
| Hazard Recognition | Micro Precision | N/A ? 0 reviewed cases |
| Hazard Recognition | Micro Recall | N/A ? not run |
| Hazard Recognition | Micro F1 | N/A ? not run |
| Hazard Recognition | Macro F1 | N/A ? not run |
| Safe-scene behavior | False-positive rate | N/A ? not run |
| Human Review | Ambiguous-case review recall | N/A ? not run |
| Regulation Retrieval | Recall@3 | 88.89% (32/36 answerable draft queries, saved pilot) |
| Regulation Safety | Unsupported citations | 0/100 returned citations, saved pilot corpus |
| Risk Policy | Correctness | 40/40 deterministic specification cases |
| Workflow | Scenario success | 20/20 isolated scenarios with injected AI |

The retrieval labels are draft judgments, not a human-reviewed formal vision set. Workflow results are mocked/unit-test results, not real AI field performance. These figures cannot substitute for missing vision accuracy. **The current evidence is not strong enough for competition claims of formal vision precision, recall or F1.**

## Preservation and verification

No product code, prompt, RiskEngine, RAG, workflow, frontend, .env or source images changed. No OpenAI or DeepSeek calls were made. Only audit/report artifacts were created or updated. Evaluation tests: **34 passed**, with existing dependency deprecation warnings; no backend or browser suite was rerun.

The existing measured summary and its original generated_at timestamp are retained. A separate openai_sol_vision_benchmark audit section was added to summary.json to prevent historical retrieval/risk/workflow results from appearing newly measured. Updated reports: docs/EVALUATION_RESULTS.md, evaluation/reports/summary.md, evaluation/reports/summary.json, this document, and evaluation/reports/openai_sol_dataset_audit.json.

Next required action is human dataset preparation, not prompt tuning or more smoke calls. Once the reviewed data is supplied, validate it and current credentials/billing, prepare the one-call-per-case runner, execute once, and regenerate all metrics and error tables from cached responses. The formal benchmark definition of done remains unmet until that work can be performed.
