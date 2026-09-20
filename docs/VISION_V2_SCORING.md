# Vision three-state scoring v1

## Implementation and compatibility

New evaluation/vision_v2_scoring.py is an offline-only manifest-aware scorer and CLI. It accepts the existing vision-v2-split-manifest-v1 schema, requires six explicit positive/negative/indeterminate decisions consistent with ground_truth_hazards, and preserves the full snapshot in its cache contract. Output is versioned vision-three-state-v1. No production code, prompts or annotations changed.

Inspection found binary assumptions in evaluation/metrics.py hazards(), report_vision_pilot.py score()/errors(), the historical HazardCase schema and the pilot/live runner paths. Legacy metrics remain unchanged for binary inputs; explicit guards reject three-state data in the binary metric/report functions. HazardCase already forbids unknown V2 fields. Do not flatten or strip class_decisions to bypass these guards. Historical run_vision_pilot.py and resume_vision_pilot.py retain their original fixed pilot/schema/prompt restrictions. evaluation/runners/vision.py is the old generic-direct versus SafeSite binary runner, not a V1/V2 split-manifest runner. None were invoked.

## Classification definitions

Successful predictions only contribute classification counts. Every planned case must have one prediction record or explicit provider_success=false record; missing/duplicate/extra IDs are errors. Failures are excluded with coverage reported, never treated as empty successful predictions.

For each class, positive and negative decisions contribute TP/FP/FN/TN; indeterminate contributes nothing to those counts. Positive support is TP+FN; evaluated sample count is TP+FP+FN+TN. Dataset eligibility and indeterminate counts are reported separately from successful-sample counts. Micro counts sum evaluable pairs. Macro precision/recall/F1 are independent unweighted averages over defined class values, with each macro denominator reported. Zero denominators produce null. A zero-positive-support class has undefined recall; its precision and F1 are zero if false positives exist and otherwise null. None of this validates positive recognition in a zero-support class.

Confirmed safe means all six decisions negative. Empty confirmed-positive labels alone never qualify. Any indeterminate decision makes a scene unknown-status for this statistic, even if another class is positive. Dataset eligibility IDs and successful safe-scene denominators are separate.

Full exact match includes only successful cases with all six decisions determinate. Partially labeled cases instead receive separately named known-label agreement: all known labels must agree, with an explicit partially labeled case denominator. Cases with zero known labels have no agreement score. Masked error attribution excludes indeterminate classes. V2 scoring emits no legacy unmasked confidence summary.

## Review metrics

Compare expected_uncertainty_review only with explicit model_uncertainty_review. Missing/null output flags are unavailable, not false. Partial availability reports its denominator. Correct/missed flags and recall use expected-review cases with available flags. Unnecessary-review rate divides flags on expected-false cases by available expected-false cases. Operational confirmation and requires_human_review never enter these calculations. Legacy V1 outputs lacking explicit uncertainty flags therefore have unavailable review metrics, with no invented mapping.

## Offline use and cache contract

From the repository root:

```powershell
backend/.venv/Scripts/python.exe -m evaluation.vision_v2_scoring evaluation/datasets/vision_v2_development_v1.json
```

Without --cache this prints eligibility only, never accuracy or F1. With --cache PATH it reads a JSON object containing scoring_schema_version, manifest_sha256 (exact file bytes), manifest_snapshot (complete unmodified V2 document) and predictions. Each prediction has case_id, provider_success, predicted_hazards for successes, and optional model_uncertainty_review. Full snapshot/fingerprint mismatch is rejected. Store run ID, provider, model, prompt version/hash and preprocessing provenance alongside the cache for reproducibility; do not overwrite old runs. Use the same manifest and scoring version for both prompts. Compare shared successful cases or explicitly disclose differing coverage; do not present different completed samples as an equivalent paired comparison.

## Manual synthetic calculation

Three cases: safe A predicts housekeeping; B has housekeeping indeterminate and the other five negative and predicts housekeeping; C has PPE positive and the other five negative and predicts PPE. Of 18 pairs, 17 are evaluable: TP=1, FP=1, FN=0, TN=15. Micro precision=1/2, recall=1, F1=2/3. Defined macro precision=(0+1)/2=1/2; recall=1/1; F1=(0+1)/2=1/2. Four classes have null precision/recall/F1. Full exact match=1/2 (A,C only). Partial known-label agreement=1/1 (B). Safe-scene false-positive rate=1/1 (A only). B is unknown-status and its housekeeping prediction is not FP. Operational confirmation=true in all prediction fixtures does not increase unnecessary uncertainty review.

## Verification and current readiness

94 evaluation tests passed, 0 failed, with two existing dependency deprecation warnings. New tests cover manual counts, both predictions for real case 008, safe/unknown scenes, exact/partial agreement, zero support, failures, missing predictions, review separation and historical hashes. Existing binary regression tests still pass; ten historical frozen evidence hashes match. Current development manifest matches the approved adjudication fingerprint.

Offline validation: 10 images, 10 reviewed, 10 structurally ready, zero missing/duplicates/errors; six unknown-site warnings retained. Eligibility: housekeeping 9 determinate + 1 indeterminate; all other classes 10 determinate. Total 59 pairs, 9 full exact-match cases, 3 confirmed safe cases (001,004,006), 1 unknown-status case (008). PPE has zero positive support. No real development accuracy metrics computed. Receipt: evaluation/reports/vision_v2_scoring_dry_run_v1.json.

Dataset and offline scoring are ready for a paired comparison. A live paired V1/V2 runner still needs to preserve this cache contract and route to this scorer; the existing legacy live commands are not compatible launch commands for the V2 split. Do not start them against this manifest or claim the live harness has been verified. No paired benchmark, paid inference or model API call occurred.
