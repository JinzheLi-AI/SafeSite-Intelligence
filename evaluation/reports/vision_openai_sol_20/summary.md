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
