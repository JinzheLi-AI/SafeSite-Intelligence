# Manual image and retrieval labeling

1. Obtain real site photographs with permission/license. Avoid exposing personal or project-sensitive information. Store approved files under an image root outside public frontend assets.
2. Replace sampling slots in hazards.json. Do not infer truth from slot descriptions, filenames or model output. Use only the six enum labels. Multiple labels are allowed; [] is a reviewed negative, null is unlabelled.
3. Have two distinct reviewers independently inspect each image without seeing predictions. Ask a qualified safety professional to adjudicate differences. Record reviewer identifiers and the rationale in notes. A photograph may not prove invisible PPE, fall protection or electrical conditions: mark ambiguous and explain the limitation.
4. Record ambiguous and expected_human_review separately. Clear visible hazards still require SafeSite human confirmation; ambiguity concerns visual evidence, not whether a human has approval authority.
5. Record image_path relative to image-root, SHA-256 of the exact bytes, license_or_consent, group_id (same site/session/near duplicates) and both reviewers. Set label_status to reviewed only after adjudication. The runner verifies metadata and file hashes; it cannot verify reviewer expertise or photographic truth.
6. Split by site/session group before tuning. Freeze labels, hashes and prompt versions before running baselines. Do not edit labels to agree with model predictions. Report class support, ambiguity distribution, negatives and multi-hazard counts in the final benchmark.
7. Review the 48 draft retrieval questions independently against stored original source passages. Mark all relevant documents/families, optionally section keywords. Add near-domain hard negatives and held-out paraphrases; existing broad out-of-domain negatives are relatively easy. Freeze final judgments before evaluation.
8. Preserve both reviewers' original annotations and an adjudication log alongside the frozen manifest. No real images or adjudicated benchmark labels are supplied in this repository.

Example reviewed record (illustrative format only, not a real benchmark observation):

```json
{
  "case_id": "IMG-001",
  "image_path": "images/site-a-001.jpg",
  "description": "Human-authored scene description",
  "ground_truth_hazards": ["working_at_height", "unprotected_edge"],
  "ambiguous": false,
  "expected_human_review": true,
  "jurisdiction": "HK-SAR",
  "notes": "Adjudicated evidence and uncertainty rationale",
  "label_status": "reviewed",
  "image_sha256": "REPLACE_WITH_ACTUAL_SHA256",
  "group_id": "site-a-session-01",
  "reviewers": ["reviewer-1", "reviewer-2"],
  "license_or_consent": "REPLACE_WITH_PERMISSION_REFERENCE"
}
```

Use `Get-FileHash -Algorithm SHA256 -LiteralPath <image>` in PowerShell. Do not set dummy hashes/permission references on actual reviewed cases. The JSON schema rejects missing required reviewed metadata and the runner rejects mismatched file hashes.
