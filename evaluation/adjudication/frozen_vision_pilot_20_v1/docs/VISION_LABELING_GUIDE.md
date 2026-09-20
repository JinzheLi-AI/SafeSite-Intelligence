# Manual labeling guide: 20-image vision pilot

This guide prepares human labels only. **No model calls or benchmark execution are part of labeling.** The manifest is [vision_pilot_20.json](../evaluation/datasets/vision_pilot_20.json): exactly case_001 through case_020. The first four slots reference the original smoke photographs without copying or renaming them. All judgments and groups start null. Sixteen slots still need photographs.

## Workflow

1. Add a real JPEG, PNG or WebP under evaluation/fixtures/ (or another declared evaluation image root). Keep the original file unchanged. Confirm permission to use it and record the source where available.
2. Set image_path relative to **evaluation/**, for example fixtures/live_smoke/01_safe.jpg. Calculate image_hash from the original bytes using `Get-FileHash -Algorithm SHA256 -LiteralPath <path>`. Do not hash a resized derivative. Set label_status to unreviewed.
3. A human reviews the actual photograph independently and fills ground_truth_hazards, ambiguous, expected_human_review, evidence_notes and reviewer. A second reviewer is **optional**.
4. Assign an intended group if useful; fill source and license_or_provenance where known. Then set label_status to reviewed. Use adjudicated only after secondary review/reconciliation actually occurred; the secondary reviewer's name may remain optional, but document the reconciliation in evidence_notes.
5. From the safesite directory, run:

```powershell
backend/.venv/Scripts/python.exe evaluation/validate_vision_dataset.py evaluation/datasets/vision_pilot_20.json
```

Use `--json` for machine-readable details. `--image-root <directory>` changes the image root explicitly; manifest paths remain relative to that root. Validation does not change labels or files and cannot make paid requests.

## What to label

Only label hazards visually supported by the image. Allowed labels are exactly missing_ppe, working_at_height, unprotected_edge, unsafe_scaffolding, electrical_hazard and housekeeping. Multiple distinct supported labels are allowed; do not repeat a label.

- **Missing PPE:** not visible does not mean missing. A fully visible head clearly lacking a helmet may support missing_ppe when the context supports the requirement. An obscured face does not establish missing eyewear. Do not assume a task-dependent PPE requirement without visible supporting context. Record uncertainty rather than a presumed violation.
- **Working at height:** require credible evidence of work at an elevated platform, scaffold or edge with fall exposure. Perspective alone is insufficient.
- **Unprotected edge:** require an open/elevated edge and absent or inadequate protection. Unclear depth is an ambiguity, not proof of a hazard.
- **Unsafe scaffolding:** scaffold presence alone is insufficient. Look for an incomplete platform, deficient guardrail, visible instability, unsafe access or an obvious structural deficiency.
- **Electrical hazard:** ordinary visible cables are insufficient. Look for exposed conductors, visible damage, unsafe temporary connections, wet/unsafe electrical equipment or a clear shock/fire-risk condition.
- **Housekeeping:** label obstructed access, clear trip hazards, dangerous material/cable clutter or unsafe debris accumulation. Normally stored construction materials alone are not a hazard.

**Safe/no supported hazard:** use ground_truth_hazards = []. This means no supported hazard can be confidently identified in the visible evidence, not that the whole site is objectively safe. Null means not labeled; never replace null with [] merely to finish a row.

**Ambiguity:** set ambiguous=true for genuinely insufficient or uncertain visual evidence, such as occluded PPE, unclear edge depth, questionable fall-arrest attachment or an unidentifiable object. expected_human_review should normally be true. Explain exceptions in evidence_notes. Record review need separately from hazard classification; human review does not make a classification correct. A clear hazard may still require operational human confirmation.

## Evidence and independence

Write evidence_notes yourself, describing visible facts and why they support the labels. Separate observations from regulatory interpretations.

Good: “Worker is standing adjacent to an elevated slab edge with no complete guardrail visible.”
Bad: “The worker violates safety law.”

Good: “Hard hat is clearly absent while the worker's head is fully visible.”
Bad: “Worker lacks required PPE.”

Never use filenames, captions, model predictions or previous SafeSite results as ground truth. Earlier model predictions exist for the first two smoke images; use a reviewer who has not seen those outputs when possible, and document prior exposure if unavoidable. The evidence examples here illustrate writing style, not labels for the four existing photographs. Do not change human labels to agree with a model later.

## Status and fields

| Status | Meaning | Required human information |
| --- | --- | --- |
| missing_image | No photograph supplied | Image/hash and human-label fields stay null |
| unreviewed | Photograph exists; human review incomplete | No automatic readiness; leave unknown judgments null |
| reviewed | Primary human review complete | reviewer, evidence_notes, hazard list (including []), both boolean flags |
| adjudicated | Secondary review/reconciliation complete | Same fields; secondary_reviewer remains optional |

For every image, fill source and license_or_provenance where available. Missing provenance produces a warning for reviewed rows, not an invented value or automatic failure. The primary reviewer is required; secondary_reviewer is optional for this pilot. Both are human identifiers, never model names.

The optional group is an intended sampling bucket: safe, ppe, working_at_height, unprotected_edge, unsafe_scaffolding, electrical, housekeeping, multi_hazard or ambiguous. Assign it manually. It is not derived from the filename and does not determine the ground truth. It is also **not** a site/session leakage-group identifier; note same-scene/session relationships in evidence_notes or source so they can be handled in a later benchmark split.

## Validation and existing-schema boundary

The validator checks exactly 20 numbered unique slots, allowed values/types, required reviewed fields, contained file paths, actual original SHA-256 hashes and duplicate byte content. Duplicate copies are excluded from benchmark-ready count, including copies whose declared hashes are wrong. Missing slots are valid incomplete entries. Unreviewed rows never count as benchmark-ready. The primary reviewer alone is enough for reviewed readiness; no two-reviewer rule is imposed.

A passing validation run means the manifest is structurally valid, **not** that every slot is ready. Benchmark-ready counts individually valid reviewed/adjudicated rows; any validation errors must be resolved before use. Warnings identify issues needing human attention. The validator cannot establish actual human authorship, photographic truth, image decoding safety, permissions or near-duplicate scene independence. Product image validation remains a separate later preflight.

The older HazardCase schema in evaluation/schema.py still requires two reviewers and has different field names/statuses. This new pilot manifest intentionally follows the requested single-reviewer policy without changing that legacy runner. Do not pass this file directly to evaluation/run.py. A future explicitly authorized pilot-runner integration must map fields/statuses without inventing a second reviewer or relaxing human-label independence. No such integration or inference is performed in this task.

## Local manual labeling interface

From the safesite directory, launch:

```powershell
backend/.venv/Scripts/python.exe evaluation/label_vision_dataset.py
```

Then open **http://127.0.0.1:8765** in your browser. Keep the terminal running; Ctrl+C stops the server. The tool uses Python's standard-library HTTP server and existing Pillow image support: no new dependency, Streamlit installation or production requirements change. It binds only to 127.0.0.1, loads no external assets and imports no model/provider or product settings code. Streamlit is absent, and this runtime's Tkinter lacks usable Tcl files, so a local browser UI is used instead. `--port 8766` selects a different local port if needed.

The original image appears on the left with literal case metadata. Click it to inspect the original in a separate tab. The right side has the six hazard checkboxes and manual review fields. No model output, caption-derived suggestions or automatic labels are displayed. Reviewer defaults to REVIEWER_1 only for a null reviewer; it is not saved automatically. Both Yes/No fields initially remain unselected. Group never changes hazard selections.

Use Save Review or Save & Next after inspecting the image and writing your own evidence. Zero selected hazards saves [] only when you deliberately save. Reviewer, evidence notes and explicit choices for both boolean flags are required. Secondary reviewer is optional. Source/provenance omissions produce existing validator warnings; group is optional. Saving an adjudicated case explicitly changes its status to reviewed, as this tool records the current primary review.

Previous, Next, case selection and filters ask before discarding unsaved edits. Filters are All, Unreviewed (including missing slots), Reviewed (including adjudicated) and Ambiguous (only explicit true). Saving under the Unreviewed filter removes the saved case from that view. Progress counts reviewed plus adjudicated cases and shows the validator's benchmark-ready count. Validate Dataset uses the same validate_dataset function as the CLI and does not save, label or run a benchmark. It reports duplicates, errors and warnings from disk; unsaved form values are not counted.

Saves update only the current row's review fields. Image paths, hashes and other rows are preserved. The complete proposed manifest is validated in a temporary file beside the original, flushed to disk and atomically replaced. Invalid or stale submissions leave the existing manifest untouched. A revision check rejects stale tabs; Reload after external edits. A short-lived manifest.json.labeling.lock coordinates saves. If the process is forcibly terminated during a save, the original is either the previous complete JSON or the newly saved complete JSON. Stop all labeling-tool instances before manually removing an orphan vision_pilot_20.json.labeling.lock; do not remove an active lock. Unreferenced .label-review-*.json files may remain after a hard crash and are not used automatically.

This tool does not launch the benchmark or bridge the pilot manifest to the older two-reviewer runner. Finish human labeling, resolve validation errors and preserve independent labels before a separately authorized benchmark task.
