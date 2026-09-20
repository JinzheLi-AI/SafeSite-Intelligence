# 10-image development-set paired comparison.

Run ID: paired_live_20260919_step16. Twenty API attempts, 20 successes, 0 failures, 10 valid pairs. Requested and returned model: gpt-5.6-sol for every call. Provider: OpenAI. Scoring: vision-three-state-v1. No retries, smoke tests, DeepSeek calls or extra inference. Durable record count and accounting receipt count both equal 20.

Dataset hash: b1a811124462f826163d673253466461123166302da1a8469a34389f749d37a6

Identical model/settings/processed bytes per pair; actual V1/V2 prompt fingerprints verified distinct. Denominators: 59 image-class pairs, 9 full exact-match cases, 3 confirmed safe scenes. Case 008 housekeeping masked; its other five labels scored; not safe and not full-exact eligible.

| Metric | V1 | V2 | V2 minus V1 (percentage points) |
|---|---:|---:|---:|
| Micro precision | 41.18% | 41.67% | +0.49 |
| Micro recall | 100.00% | 71.43% | -28.57 |
| Micro F1 | 58.33% | 52.63% | -5.70 |
| Macro F1 | 59.52% | 43.97% | -15.56 |
| Safe-scene FP rate | 100.00% | 33.33% | -66.67 |
| Full exact match | 22.22% | 44.44% | +22.22 |

| Class | Positive support | V1 P/R/F1 | V2 P/R/F1 | V1/V2 FP | V1/V2 FN |
|---|---:|---|---|---|---|
| missing_ppe | 0 | 0.00% / N/A / 0.00% | 0.00% / N/A / 0.00% | 1/1 | 0/0 |
| working_at_height | 1 | 100.00% / 100.00% / 100.00% | 25.00% / 100.00% / 40.00% | 0/3 | 0/0 |
| unprotected_edge | 1 | 33.33% / 100.00% / 50.00% | 100.00% / 100.00% / 100.00% | 2/0 | 0/0 |
| unsafe_scaffolding | 1 | 100.00% / 100.00% / 100.00% | N/A / 0.00% / 0.00% | 0/0 | 0/1 |
| electrical_hazard | 2 | 40.00% / 100.00% / 57.14% | 100.00% / 50.00% / 66.67% | 3/0 | 0/1 |
| housekeeping | 2 | 33.33% / 100.00% / 50.00% | 40.00% / 100.00% / 57.14% | 4/3 | 0/0 |

Macro means include defined class values separately for each metric; undefined denominators are null. Missing PPE has no positive support, so its zero F1 reflects false positives, not validated positive recognition.

## Review

V2: expected uncertainty review 2; correct flags 1; missed 1; recall 50%; unnecessary flags 5/8 = 62.5%. V1 explicit uncertainty metrics unavailable and incomparable; aggregate operational review was not substituted.

## Case changes

- Improvements: 004 and 006 no longer receive electrical false positives; 004 also loses its housekeeping FP. 007 loses electrical FP. 001 loses unprotected-edge FP but retains housekeeping FP.
- Regressions: 003 misses its electrical positive; 005 misses unsafe scaffolding and adds working-at-height FP; 008 adds working-at-height FP (housekeeping remains unscored).
- Mixed: 010 replaces unprotected-edge FP with working-at-height FP. Unchanged PPE FP and housekeeping FP on 009.
- V1 TP/FP/FN = 7/10/0; V2 = 5/7/2. Reduced false positives do not establish overall improvement: recall and F1 declined.

## Usage and latency

```json
{
  "total": {
    "input_tokens": 42450,
    "output_tokens": 17103,
    "total_tokens": 59553,
    "mean_latency_ms": 18293.9,
    "median_latency_ms": 18162.5
  },
  "vision-v1": {
    "input_tokens": 20130,
    "output_tokens": 8474,
    "total_tokens": 28604,
    "mean_latency_ms": 17951.3,
    "median_latency_ms": 18494.0
  },
  "vision-v2": {
    "input_tokens": 22320,
    "output_tokens": 8629,
    "total_tokens": 30949,
    "mean_latency_ms": 18636.5,
    "median_latency_ms": 16906.5
  },
  "estimated_cost_usd": null,
  "pricing_note": "No reliably applicable configured price produced a cost in any call record; no dollar estimate fabricated."
}
```

Latency measures runner invocation elapsed time, milliseconds; provider accounting latency is retained separately in call_records. Estimated USD unavailable.

## Verification and limitations

Metrics and paired report reproduced byte-for-byte offline with socket connections blocked; zero additional API requests. Generated JSON parsed successfully. 111 pre-existing protected files match preflight hashes, including labels, image files, prompts, held-out data and historical results. Preflight DNS/TLS succeeded (unauthenticated HTTPS 401). Credential presence verified without printing secrets.

Safety-only runner fix before execution: immediate stop on credential, quota/rate-limit, model-access and schema/request-compatibility failures; new mocked regressions passed. No prompt/scoring changes.

This is a 10-image development-set comparison, not independent validation or production accuracy. Primary annotations included AI-assisted discussion, without secondary adjudication. Small class support and unknown sites limit generalization. No statistical significance claim.

Recommended next step: offline audit of V2 missed electrical/scaffolding positives and working-at-height false positives; preserve both prompts. Do not launch another benchmark or tune on held-out results.

Post-execution evaluation regression: 102 passed, 0 failed; two existing dependency deprecation warnings.
