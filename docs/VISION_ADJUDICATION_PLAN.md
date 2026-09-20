# Vision Adjudication Plan

Date: 2026-09-18. Preparation only; no label decisions, production changes, inference or metric recalculation.

## Artifacts and scope

- Proposed protocol: [VISION_LABEL_PROTOCOL_V2.md](VISION_LABEL_PROTOCOL_V2.md), ID `vision-label-protocol-v2.0-proposed`.
- Facilitator queue: [vision_pilot_20_review_queue.json](../evaluation/adjudication/vision_pilot_20_review_queue.json).
- Frozen originals: [frozen_vision_pilot_20_v1](../evaluation/adjudication/frozen_vision_pilot_20_v1/).

**20 pending cases: 10 priority adjudications and 10 comparison/consistency reviews.** Priority: 007, 003, 004, 010, 011, 014, 015, 017, 019, 020. Comparisons: 001, 002, 005, 006, 008, 009, 012, 013, 016, 018. Every original case is included so changed definitions are not applied only to errors or chosen to raise scores. All decisions, rationales, reviewer assignments and completion timestamps start null; all statuses are pending. Comparison cases are not presumed correct.

## Freeze and provenance

Original dataset: evaluation/datasets/vision_pilot_20.json. Original run: evaluation/reports/vision_openai_sol_20_20260918_01/. Copies preserve the dataset and every file in that completed run, including predictions, metrics, case errors, report, interpretive notes, verification and lock. The prior audit and labeling guide are also copied with their original relative paths under frozen_vision_pilot_20_v1/. Source and snapshot bytes were compared; their SHA-256 values are embedded in the queue. The image files remain in place, untouched, with all 20 hashes verified and registered in the queue. A hash-backed snapshot is an integrity record, not a filesystem permission lock; treat it as read-only and verify before use.

The original pilot was single-primary-reviewer, involved AI-assisted annotation discussion, was not fully blind, and had no secondary adjudication. Four images were reused from smoke testing. The existing numbers remain historical evidence: precision 48.28%, recall 93.33%, micro F1 63.64%, safe-scene FP rate 42.86%, unnecessary-review rate 75%. They are not recomputed in this task.

Any revised labels belong in a separately versioned dataset, for example evaluation/datasets/vision_pilot_20_adjudicated_v2.json, with parent dataset hash, protocol hash/version, actual reviewer identities and exposure history. That file is NOT created or populated here. Revised scoring on already evaluated images would be retrospective reanalysis, not a new independent benchmark. Do not claim improvement from definition changes alone. A new independent test would require separately collected, held-out, appropriately reviewed images and separately authorized inference.

## Human review sequence

1. **Approve semantics before opening case results.** Agree on the six definitions and explicitly accept or amend the elevated-activity meaning of working_at_height. Establish which supplied site context, if any, annotators may use. Do not inspect benchmark scores to choose definitions. Record protocol approval and freeze its version before collecting decisions.
2. **Assign a qualified secondary reviewer and disclose exposure.** Prefer someone who has not seen previous labels/predictions. Record prior exposure; do not describe a previously exposed reviewer as blind. Have a facilitator manage the queue. New task-specific PPE context must be authenticated and declared; do not invent it to resolve a disagreement.
3. **Independent pass, before old labels and predictions.** Supply the generic protocol with dataset case references/examples concealed. Show original photographs with neutral case IDs, in a mixed order. Use an ordinary local image viewer; no new UI is needed. The facilitator opens images so semantic filenames such as safe/obvious_hazard are not used as guidance. Do not present original label values, group, human notes, error questions, audit, run summary, or the raw queue JSON at this stage: all can anchor a reviewer. The initial pass records each of six positive/negative/indeterminate decisions, concrete evidence, A/B/C review concepts, rationale, identity and date in a separate human-authored worksheet following the proposed schema. Null means unfinished, never an implicit negative.
4. **Lock the independent record.** Preserve that worksheet with a timestamp and hash before revealing anything else. The facilitator can then enter its content into the queue's reviewer_decision/reviewer_rationale fields verbatim. Do not generate or infer decisions with AI. A completed independent review is not yet secondary adjudication.
5. **Human reconciliation before model reveal.** Reveal original labels/notes, comparison cases and the queue's precise questions. Ask whether disagreements arise from new definitions, overlooked visible evidence, uncertain context or genuine unresolved interpretation. Record a reconciliation rationale, including why any original label is retained or changed. Keep the independent judgment intact; do not overwrite it with the reconciled result.
6. **Optional model-output reveal only after human judgments are preserved.** A facilitator may show cached predictions to explain historical errors, with the time and extent of exposure logged. No fresh inference. Any changed opinion after reveal is a separate post-exposure revision, not a blind judgment. Agreement with the model is not an acceptance rule.
7. **Finalize only resolved cases.** Suggested queue transitions: pending -> independently_reviewed -> adjudicated; use unresolved when evidence cannot settle a disputed class. Adjudicated requires actual qualified secondary reconciliation with names, date and rationale; neither a filled first-review field nor an automated validation check is sufficient. Keep indeterminate classes explicit; do not force consensus or silently map to [].
8. **Publish a new annotation version only after approval.** Retain original labels, independent judgments, reconciliation record and context provenance. Validate the proposed v2 schema with its own later validator before use; the existing pilot validator does not understand the three-state/new review fields. Record per-class resolved coverage and unresolved cases in any future analysis. No scoring is part of this preparation task.

## Focused reconciliation questions

- **PPE requirement:** 007 against 006/008/013; absence AND contextual requirement must both hold. 003/004/014 provide headwear comparisons, 020 a tool-context question, 017 a footwear/role question. Do not automatically accept the old AI-assisted label.
- **Height definition:** compare 003 with 009/011/012/015/019/020 under the explicitly proposed elevated-activity definition. Visible protective measures do not erase the activity label, and the activity label does not imply defective protection.
- **Specific scaffold defect:** inspect 010 against 009/011/012/019. Identify the actual defective component; missing visibility is not a defect.
- **Electrical condition:** 015 and 017 against 013/016. Specify a visible unsafe interaction rather than assuming energization or lack of insulation. Existing zero positive support remains an evaluation limitation.
- **Housekeeping mechanism:** 004/007/011/014 against 016/017. Locate actual walking/work-surface interference or unsafe storage, not merely construction materials.
- **Review concepts:** compare 015/019 with 009/011/012/020, and 016 with 018. A clear positive may need operational confirmation without perceptual uncertainty. Unknown global site conditions do not automatically establish a concrete safety ambiguity.

## Reuse the existing UI safely

Existing tool: evaluation/label_vision_dataset.py. It supports --manifest, --image-root and --port. It does not show model output, but DOES show and prefill existing human labels and evidence notes. It writes to the manifest selected at launch and defaults to the historical original. It also marks saves reviewed, rather than performing adjudication. It cannot represent indeterminate class targets or the three separate proposed review concepts.

Therefore **do not launch it with its defaults for this adjudication, and do not use a prefilled copy for the initial independent pass**. No UI was changed or started in this task.

After independent records are locked, it can optionally serve as an image browser or legacy-field editor against a separately prepared disposable working copy. Its legacy ambiguous and expected_human_review fields must not be used as substitutes for the new A/B/C fields. Keep full v2 decisions in the queue/worksheet; do not save through the legacy form if it would force an unresolved class into a binary label. A valid legacy working copy may be prepared by the facilitator in a later authorized review task; none is generated now.

Example, from safesite, **only after that separate working copy exists**:

```powershell
backend/.venv/Scripts/python.exe evaluation/label_vision_dataset.py --manifest evaluation/adjudication/working/vision_pilot_20_legacy_working_copy.json --image-root evaluation --port 8766
```

The image-root argument keeps the original fixture paths valid while edits target the working copy. Verify the selected path before saving. The existing /guide link points to the OLD labeling guide; open docs/VISION_LABEL_PROTOCOL_V2.md separately and use the approved version. Do not mistake a UI save, a passing old validator, or its benchmark-ready counter for completed v2 adjudication.

## Proposed review fields and reporting

- A: perceptual_uncertainty + uncertain_facts — what the image cannot establish.
- B: requires_safety_adjudication + adjudication_reason — concrete need for qualified interpretation.
- C: operational_confirmation — required/not_required/not_applicable under an explicit business policy, separate from A/B.

All start unset. No automatic migration from old ambiguous/expected_human_review, production requires_human_review or RiskEngine output. An operational confirmation annotation does not execute an incident confirmation. Preserve current product guardrails until a separately authorized design change is reviewed. Full proposed schema and per-class decisions appear in the protocol.

## Verification performed

- Queue parsed as valid JSON; exactly 20 unique existing cases, including all 10 requested priority cases.
- All reviewer decisions/rationales null and all statuses pending; no fabricated review identities or completion timestamps.
- Original annotation fields match the dataset; no model predictions embedded in the queue.
- All 20 image hashes match. Snapshot files are byte-identical to originals with SHA-256 records.
- No historical scores recalculated; no production prompt, RiskEngine, RAG, model output, source image or ground-truth edit.
- Zero OpenAI calls, zero DeepSeek calls, zero paid calls. No benchmark or regression inference runner executed. Documentation/data-only consistency checks were sufficient for this preparation.
