# Case 008 human-approved adjudication, version 1

Only the five explicitly approved fields in v2_development_008 were updated: housekeeping positive -> indeterminate; ground_truth_hazards [housekeeping] -> []; ambiguous, expected_uncertainty_review and requires_safety_adjudication false -> true. The other five class decisions, notes, operational confirmation, review status and every other case are unchanged.

Reason: the actual image and corrected notes do not establish whether the foreground conduit obstructs an accessible route. The V2 protocol requires abstention for an unclear route/exposure mechanism. An empty ground_truth_hazards list records no confirmed positives, NOT a confirmed safe scene. This is a user-approved uncertainty correction, not completed secondary adjudication.

The full original and corrected annotations, authorization, reason and pre-change manifest fingerprint are preserved in evaluation/reports/related_review_20260919/case_008_adjudication_v1.json. Validation and post-change fingerprint are in case_008_adjudication_v1_validation.json. Preservation checks verified 101 other files unchanged and an exact five-field-only annotation diff.

## Offline validation

10 images, 10 reviewed annotations, 0 missing, 0 duplicate images, 0 validation errors, 10 structurally benchmark-ready. Six existing unknown-site warnings remain. The annotation validator permits indeterminate decisions with explicit uncertainty; its readiness count does not verify evaluator compatibility.

## Confirmed evaluation blocker

- evaluation/metrics.py: hazards() builds expected labels exclusively from ground_truth_hazards and counts every class; it has no indeterminate mask.
- evaluation/schema.py: HazardCase has no class_decisions field and forbids extras. It cannot directly represent V2 per-class uncertainty. Do not strip V2 fields to force compatibility.
- evaluation/report_vision_pilot.py: score() treats every absent label as negative and defines safe scenes using an empty ground_truth_hazards list. Its case-error and confidence attribution also use that binary assumption. It would count case 008 as safe after an unsafe lossy conversion and count a housekeeping prediction as a false positive.

No scoring code was changed, no prediction scores were calculated and no live runner executed. Current tooling is NOT ready for a valid paired V1/V2 development evaluation despite 10/10 structural dataset readiness.

## Proposed minimal versioned evaluator fix (not implemented)

Preserve V2 class_decisions through loading, saved snapshots and cached predictions. Apply a per-case/per-class eligibility mask: score only positive or negative decisions; indeterminate contributes neither TP, FP, FN nor TN for that class. Retain the other five determinate labels on case 008. Aggregate micro/macro scores from those masked counts and report denominators/excluded counts. Define confirmed safe scenes as all six decisions explicitly negative, never merely an empty positive list. Exclude partially indeterminate cases from full six-class exact-match scoring (report coverage separately). Apply the same mask to error attribution and confidence summaries. Score uncertainty review separately from operational confirmation, using expected_uncertainty_review. Keep legacy V1 pilot behavior unchanged in its historical schema/path.

Add offline tests proving that either housekeeping prediction on case 008 is excluded from that class, that it never enters the confirmed-safe denominator, that its other five classes remain scorable, and that genuine all-negative scenes do enter the safe denominator. Verify identical paired sample/mask definitions for V1 and V2 and preserve indeterminate labels in cached result round trips. Only after this fix and tests should evaluation proceed.

Zero model API calls. Production prompts and historical results unchanged.

Relevant offline tests: 45 passed, 0 failed (annotation V2 application, evaluation metrics/schema and pilot reporting tests). Passing existing tests does not establish V2 scoring compatibility; the unsupported behavior above remains a blocker.
