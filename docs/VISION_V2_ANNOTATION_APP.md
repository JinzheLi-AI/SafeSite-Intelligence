# Local V2 annotation application

Step 11 implements dataset selection, local import, V2 annotation, validation and held-out freezing in the existing annotation website. It makes no model calls. Historical pilot data is read-only. Development and held-out manifests remain separate; no images or annotations are generated for them.

## Launch on Windows

```powershell
& '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite\backend\.venv\Scripts\python.exe' '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite\evaluation\label_vision_dataset.py' --port 8766
```

Open http://127.0.0.1:8766. If this instance is already running, open its URL instead of launching another process on the same port. The server binds only to loopback.

## Import and annotate a photograph

1. Select **V2 development**, then an empty case.
2. Choose a local JPEG or PNG (maximum 10 MiB) and click the import button. Decoded content is validated; corrupt, unsafe or multi-frame images are rejected. Original bytes are preserved under `evaluation/fixtures/vision_v2/development/` or `heldout/`, using the SHA-256 as the filename. Existing images cannot be replaced through this tool.
3. Enter source and permission information that you can verify. Leave unknown identities unknown. Record known site/scene grouping and original-image identifiers, and review related-image leakage. Exact duplicates are rejected across all three datasets; known matching groups or source identifiers cannot be saved across splits. Different hashes do not establish scene independence.
4. Use `docs/VISION_LABEL_PROTOCOL_V2.md`. Choose positive, negative or indeterminate for each of the six classes. All-negative decisions persist an empty hazard list. Indeterminate decisions require ambiguity and uncertainty review. Keep uncertainty, safety adjudication and operational confirmation separate.
5. Enter visual evidence, your reviewer name and the review flags. Save drafts as unreviewed; choose reviewed only when complete. Adjudicated status requires a secondary reviewer. No review status is assigned automatically by the model or the application.
6. Click Save, then Validate. Validation checks actual image bytes/hashes, duplicate/group leakage and annotation completeness. Missing image slots remain explicit validation errors until filled.

## Held-out freeze

Select V2 held-out and complete all target cases. Freezing additionally requires verified permission with supporting provenance/evidence and completed related-image reviews. Click Freeze and acknowledge the held-out safeguards. Incomplete datasets cannot freeze. The server rejects both imports and annotation edits after freezing, independent of disabled browser controls.

The manifest records a timestamp and SHA-256 of canonical UTF-8 JSON excluding `frozen_manifest_sha256`. Validation checks this fingerprint. There is no implicit unfreeze action. This is application-level integrity protection, not a filesystem access-control system. Restrict access to held-out images and labels separately during prompt iteration; the annotation UI itself is not a blinding mechanism. Indeterminate labels must remain explicit in later evaluation and must not silently become negative labels.

Saves use revision checks, a shared dataset write lock and atomic manifest replacement. If another editor saved first, reload before retrying. Do not delete a lock while a writer is active.

## Offline verification

`backend/.venv/Scripts/python.exe -m pytest evaluation/tests -q`: **86 passed, 0 failed**, with two deprecation warnings.

The new HTTP integration tests create synthetic PNG/JPEG images only in temporary datasets. They demonstrate import through the handler, byte-preserving storage, annotation persistence, validation, duplicate rejection and rejection of imports/edits after freeze. They also cover corrupt uploads, request authorization, historical read-only behavior, incomplete freeze, stale revisions, indeterminate decisions and cross-split grouping rejection.

A local browser check verified the dataset selector, historical read-only controls, six V2 class controls, editable import controls, held-out freeze control and validation action. All three real manifests were byte-identical before and after this check. Neither real V2 dataset received a test image. No paid or external model API calls, downloads or benchmark execution occurred.
