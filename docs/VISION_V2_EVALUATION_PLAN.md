# Vision V2 evaluation dataset preparation

Date: 2026-09-18. No inference executed. This plan supersedes the earlier suggested larger collection targets with the requested **10 development + 20 held-out** design. Neither prompt version is modified.

## Current inventory and readiness

| Split | Target slots | New images registered | Human-reviewed | Ready | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Development v1 | 10 | 0 | 0 | 0 | Awaiting collection |
| Held-out v1 | 20 | 0 | 0 | 0 | Awaiting collection; NOT frozen |

Manifests:

- evaluation/datasets/vision_v2_development_v1.json
- evaluation/datasets/vision_v2_heldout_v1.json

These are empty dataset templates containing stable case slots, not 30 acquired photographs. All image paths/hashes, human labels, review flags, evidence, source/license information and reviewer identities are null. No image has been assigned a class to meet a quota. Slot status is missing_image, not reviewed. Known site/scene identities are absent and explicitly marked unknown.

The project-owned inventory search covered evaluation/, backend/uploads/, backend/data/, frontend/public/ and docs/, excluding installed dependencies and build caches. It found 29 image files: all 20 historical photographs plus nine ancillary PNG assets (UI/documentation/knowledge assets without established new-photo eligibility). **Zero genuinely new eligible evaluation photographs were found.** This is a scoped local finding, not a claim about external or personal libraries. The nine nonmatching hashes are not assumed to be independent scenes or usable construction photographs.

Exact SHA-256 inventory: evaluation/reports/vision_v2_collection_audit_v1.json. The 20 historical photographs match the excluded pilot manifest. No exact duplicate groups occur among the 29 inventoried files. New development/held-out duplicates are zero only because both contain zero images; related-scene review is incomplete, and independence is not certified.

## Collection checklist and leakage control

1. Collect **30 new permitted photographs** through user-owned/site-authorized material or a source whose terms permit the intended use. Start with electrical-hazard candidates, but never create dangerous conditions to obtain an example. No third-party downloads or scraping were performed here, and no source or license is presumed from a filename/platform name.
2. For each candidate, record a direct source URL and original-image identifier where available, source platform, the original construction-site/scene identifier if actually known, acquisition details and verifiable permission/license evidence. A website name is not a construction-site identity. Keep unknown values null with identity status unknown; do not invent a unique site for each file. Rights unresolved means ineligible for release/evaluation until resolved.
3. Place approved originals under evaluation/fixtures/vision_v2/development/ or evaluation/fixtures/vision_v2/heldout/ AFTER group assignment. These are proposed locations, not existing populated directories. Preserve bytes and EXIF; use production preprocessing later without overwriting originals. Store image_path relative to evaluation/ and the SHA-256 of original bytes.
4. Compare hashes against the original 20, frozen/other known development exposures, and all new candidates. Reject historical matches and new exact duplicates. Hashing catches neither resized/cropped copies nor separate frames from the same scene. Compare source original-image IDs, photographer series, site/session identifiers and visually inspect near duplicates.
5. Assign each known site/scene/session group wholly to one split, never by individual image. Related crops/angles from an unknown site still share a human-documented related-image group when evidence supports it. Record the grouping basis; it is not an invented site identity. Where group identity is unknown, retain unknown and record a manual relatedness review. Quarantine ambiguous cross-split relationships; do not default every unknown to a different scene or claim proven site independence.
6. Use an independent data custodian to assign held-out groups before prompt iteration. If a held-out image/group is accidentally used during development, retire it from held-out status and replace its group with genuinely unexposed data; log the change rather than quietly moving related frames.
7. Verify full image decoding and unchanged production preprocessing offline. Reject corrupt or unsafe files using existing prepare_image; do not call a model to establish suitability or labels.
8. Fill only metadata known from evidence. Image registration is not annotation: labels stay blank until a human completes review. No need to repeat the historical 20-image labeling exercise.

## Coverage goals, not automatic labels

| Coverage dimension | Development collection aim (10) | Held-out collection aim (20) | Current verified coverage |
| --- | --- | --- | --- |
| missing_ppe | At least 1 supported positive and requirement/visibility negatives | At least 2 supported positives, plus negatives | Unavailable: no images/reviews |
| working_at_height | At least 1 elevated-activity positive; include guarded context | At least 2 positives with varied controls | Unavailable |
| unprotected_edge | At least 1 supported positive; unclear-depth comparison | At least 2 supported positives | Unavailable |
| unsafe_scaffolding | At least 1 specific-defect positive; ordinary scaffold comparison | At least 2 supported positives | Unavailable |
| electrical_hazard | Prioritize at least 2 actual unsafe-condition positives | Prioritize at least 3 actual unsafe-condition positives | Unavailable; historical positive support was zero |
| housekeeping | At least 1 clear obstruction/slip/trip positive | At least 2 supported positives | Unavailable |
| Supported empty scenes | At least 2 | At least 5 | Unavailable |
| Concrete ambiguous/uncertainty cases | At least 2 | At least 4 | Unavailable |

Multi-label and ambiguity overlap make these collection aims possible within 10/20; they are not disjoint quotas and are not guarantees. Humans decide labels from evidence. If coverage cannot be met, record actual support/coverage and obtain a scope decision before evaluation rather than forcing a label or exceeding the image count silently. Two or three positives per class remain weak evidence; this is still a small evaluation.

## Annotation fields and rules

Use docs/VISION_LABEL_PROTOCOL_V2.md (protocol ID and source hash recorded in each manifest). The document is explicitly proposed; record human acceptance of its definitions before annotation/inference. Elevated work activity does not automatically mean an uncontrolled fall hazard. Required PPE needs visible absence AND observable requirement; explicit site-only context unavailable to the model must be separately recorded and must not silently become an image-only target.

Each row includes case ID, path, original hash, source URL/platform/original image ID, verified provenance/permission evidence, site/scene/group identifiers, ground_truth_hazards, six class_decisions, ambiguous, expected_uncertainty_review, requires_safety_adjudication, operational_human_confirmation, evidence notes, reviewer, secondary reviewer, prior exposure and review status.

- Null means unknown/unanswered. ground_truth_hazards=[] is allowed only after human review confirms no supported positive; it is not the default for an empty slot.
- class_decisions values after review are positive/negative/indeterminate. For unresolved class judgments, retain indeterminate; do not encode them as a false negative or silently exclude them. A future scorer must report class eligibility masks and eligible denominators. Cases with any indeterminate class are not eligible for full exact-match or confirmed-safe metrics.
- ground_truth_hazards, when populated by a human, lists supported positives and must agree with positive class_decisions. It must not imply all other classes are negative when indeterminate decisions exist.
- ambiguous records concrete perceptual ambiguity; expected_uncertainty_review targets V2 model_uncertainty_review. Human safety adjudication and operational_human_confirmation are separate fields; an unambiguous hazard can require operational confirmation without uncertainty. Do not backfill them from the historical requires_human_review aggregate.
- Record evidence and rationale per class in evidence_notes or a versioned sidecar, including uncertain facts and requirement sources. No fabricated contextual rules, sources, rights, reviewers or adjudication status.
- Review status lifecycle: missing_image -> unreviewed after authorized registration -> reviewed after a complete primary record -> adjudicated only after actual secondary reconciliation. Unresolved questions remain explicit. Marking reviewed does not prove consent, provenance or site independence.
- Prefer qualified independent review and secondary adjudication for all held-out cases. If only one reviewer is available, disclose that limitation before approval; do not label the data independently adjudicated.

## Existing tools and reuse limits

No dedicated permission-aware image acquisition tool was found in evaluation tooling. Existing tools support local manual annotation, offline pilot validation, image preprocessing, cache-based reporting and guarded live inference. Do not invoke a live runner during collection.

The local evaluation/label_vision_dataset.py UI can display original images and capture legacy six-class annotations, but its validator requires the original 20-case array/IDs. It cannot directly edit these versioned 10/20 split objects or represent the separate review concepts/indeterminate states. Its default points at the historical dataset and its guide link is the old guide. **Do not pass these manifests to it or launch the default to label new data.** Reuse its image-viewing/form/atomic-write components in a separately authorized small adapter later, or use a local image viewer and human-edited manifests now. No new interface or product feature was built here.

The old validate_vision_dataset.py and historical run/report commands likewise do not validate/run these new schemas. Their logic can be reused in a future split-aware validator/paired runner; no new live runner is prepared or executed in this task. This preparation includes JSON/placeholder/hash consistency checks, not a claim that existing benchmark tools can already consume the new files.

## Held-out safeguards and freeze

A local filename or split flag is not access control. These current blank templates may remain in the shared repository. Once held-out images/labels exist, the data custodian should keep the populated held-out manifest, photos and reconciliation notes outside the prompt-iteration workspace in a restricted location; developers receive only IDs/counts and nonrevealing readiness information. Do not commit private held-out labels to a shared branch visible during iteration. Prevent prediction/report previews from exposing held-out content before final freeze.

Use development images only for debugging and prompt iteration. Log development prompt versions and exposure. Before any final run, freeze prompt bytes/code, image bytes, manifest, protocol, annotations, grouping decisions, preprocessing/config and metric definitions. Verify both splits against historical hashes and scene groups again. The held-out frozen flags remain unset now because nothing is ready.

Freeze after images, permissions, grouping and human labels are complete: record frozen_at and status, then hash the finalized manifest and store the digest in a separate immutable freeze record with all file hashes. Do not put a hash of a file inside the same file and create a self-reference; frozen_manifest_sha256 in the current template is reserved/null and should remain null when the external freeze record is authoritative. Archive byte-identical versions and retain original records. Any later change creates a new version and invalidates the old run's comparability, not the historical record itself.

## Future paired comparison and approval checkpoint

**Current authorized inference count: zero.** A later approval must specify exact eligible image IDs, split hashes, two prompt hashes, model/provider, run IDs, maximum attempts and budget. Stop before paid execution and obtain explicit approval; this document is not that approval.

Proposed counts for a single pass:

- Optional paired development comparison: 10 images x 2 versions = **20 inference attempts**. Alternatively V2-only development pass = 10; choose explicitly before approval. Each further iteration requires its own disclosed count/approval.
- Final held-out comparison: 20 images x 2 versions = **40 inference attempts** total, one per image/version, no automatic retries. If using a checkpoint, its calls are INCLUDED in 40; do not add an extra smoke call.
- If both one paired development pass and final comparison are approved: **60 total attempts**, not a recurring allowance. No monetary estimate is supplied without reliable dated pricing and actual/configured usage assumptions.

Use the same gpt-5.6-sol model, OpenAI provider, production preprocessing bytes, language, structured output schema, output token limit, timeout policy and evaluation definitions for both versions. Only prompt version and its intentionally versioned review normalization differ. Record requested/returned model, prompt/code hash, raw uncertainty flags and normalized review flags. No silent model substitution. Run sequentially or conservatively with balanced order to limit temporal effects; keep model changes during the run visible as a comparability limitation.

V1 has no separate normalized model_uncertainty_review signal. Prespecify a proxy based on its raw model requires_human_review (with raw ambiguity also reported), or report the V1 metric unavailable; do not compare V1's aggregate mandatory-confirmation field with V2 uncertainty as if they were identical. Report operational/aggregate metrics separately. Classification uses raw categories, never RiskEngine scores. Both versions use the same held-out human labels and class masks.

Durably cache each normalized/raw result and attempt receipt immediately, keyed by run ID + case + prompt hash + image hash. Skip all recorded attempts on resume, including uncertain outcomes pending investigation. No automatic retry or mock substitution. Stop on failed first checkpoint, credential/billing/model access failure or two consecutive network failures. Preserve failures and coverage; never score a failed call as an empty prediction. Regenerate reports offline from cache.

Report micro/per-class precision/recall/F1, exact match on fully resolved cases, safe-scene FP rate, uncertainty recall/unnecessary-review rate, coverage, failures, tokens and latency. Zero-positive class recall is N/A, not demonstrated success. Preserve both successes and failures and eligible denominators. Do not compare V2 on new data against only historical V1 metrics. Once final held-out results are revealed, do not tune V2 and call a rerun a fresh independent test; obtain a new untouched test set for any such claim.

## Remaining manual work and exact next step

Appoint a data custodian and collect the first batch of **new, permitted electrical-safety candidate photographs plus ordinary-equipment negatives**, recording source URL/original-image ID, permission evidence and any known site/scene group. Then collect the remaining categories, safe scenes and ambiguous examples to fill 10/20 without shared sites/scenes. Register bytes/hashes without labels first. Keep held-out candidates away from prompt development. Annotate only after the protocol is accepted; no need to repeat historical manual labels.

No images were downloaded, no labels were inferred, and no historical prompt/dataset/report was changed. Both sets remain NOT READY. Current JSON and original-hash integrity checks pass; this does not establish future annotation validity, rights or independent scenes.
