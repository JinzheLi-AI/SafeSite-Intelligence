# Proposed GitHub publication review

Date: 2026-09-20. Target repository name: SafeSite-Intelligence. Connected account confirmed as REVIEWER_1Li-AI. **Not published; no public repository or commit hash is claimed. Explicit owner approval is required before public creation/upload.**

## Existing project and preservation

Work was performed inside the original SafeSite folder. No replacement application was reconstructed. The parent workspace, not SafeSite itself, owns the existing .git directory. It has zero reachable commits and no tracked SafeSite files. That parent also contains unrelated projects and must not be uploaded. No parent Git metadata, remote, branch or original project file was deleted or rewritten for publication.

The README was refreshed after preserving its original in ignored `.publication/README.before-publication.md`. Production source, prompts, datasets, historical reports, images, database and environment secrets are unchanged. The only original-file edits are README and .gitignore; publication scripts/docs/tests were added.

## Concrete review artifacts

Run `backend/.venv/Scripts/python.exe scripts/prepare_publication.py` from the project root. This offline tool produces:

- `.publication/inventory.json`: every proposed file, include/hold/exclude decision, source and publication hash for included files, privacy-redaction flag and Git audit counts.
- `.publication/SafeSite-Intelligence-review.zip`: a review archive directly from the original files, not another working repository. It contains no .git and is not uploaded.
- `.publication/PUBLICATION_INVENTORY.md`: human-readable inventory generated for approval alongside the machine manifest.

The complete backend/frontend/evaluation/shared/startup implementation is retained, including lockfiles, existing tests, annotation tools, prompts and cached numerical results. Ten development photos have file-specific permission records and credits in THIRD_PARTY_MATERIALS.md. Withheld pilot images mean this proposed package is not a complete reproducible historical image dataset; obtain permission/source evidence to include them, or explicitly approve that exclusion. No substitute images or invented results are used.

## Exclusions and unresolved questions

1. Twenty pilot photos lack file-specific source/creator evidence. Five screenshots and two contact sheets remain held for embedded-image/privacy review. All originals remain local.
2. API keys, all real .env variants, private databases/uploads, downloaded regulatory PDFs/model weights, caches, logs, traces and local integrity receipts are excluded. Blank .env.example files are included. No PDF redistribution grant is inferred.
3. Public copies redact local home paths and reviewer identities. Original labels, decisions, numerical results and prompts are preserved. Redacted copies have different hashes; original audit hashes describe the preserved local evidence, not these sanitized copies. Human labels are not reassigned or re-reviewed.
4. No project-wide software license exists. No new license has been selected on the owner's behalf. Approval may retain rights reserved or explicitly select a license; third-party licenses remain separate.
5. Some historical docs and source scripts reference the withheld smoke/pilot images. The browser ambiguous-image test and uncertainty helper require those files locally. They are not silently changed or skipped to create a misleading clean-clone pass.

## Security and history audit

Known configured secrets were compared in memory without printing them. The candidate files and resulting ZIP were checked for those values, provider/GitHub token patterns, private-key markers, credential-bearing URLs and AWS key patterns. Any detected candidate is held rather than automatically published. This is a bounded pattern/exact-value audit, not proof that every unknown secret or private fact can be detected.

All parent Git objects, including unreachable objects, were scanned. Initial scan: 1,329 objects (1,176 blobs, 153 trees), zero configured-key/pattern findings, zero reachable commits, and fsck exit 0. There were 951 dangling-object notices; these are not committed history or corruption. Counts can grow as the editor records subsequent changes; the final inventory records the latest scan. None of these objects will be copied or pushed.

The connected GitHub identity was read only. There is no GitHub CLI installed on PATH, and the exposed connector has file/commit APIs but no repository-creation method. After approval, repository creation may require the connected GitHub website or another available authenticated route. Account access is confirmed; creation capability has not yet been proven. No credential is extracted from a browser or connector.

## Checks and scope

Publication tests exercise exclusion rules, lockfile inclusion, explicit media holds, non-disclosing secret detection and valid JSON privacy redaction. Final integrity checks compare original protected files, verify ZIP CRCs and per-file hashes, parse Python/JSON, and verify that backend application/frontend source bytes are unchanged in the proposal. Results and exact inventory totals are recorded in the local approval inventory.

No dependency installation, vulnerability remediation, production behavior change, live benchmark or model inference is part of this task. Earlier Day 1 acceptance counts remain historical; they are not represented as new clean-clone tests. No project-wide software license or security/redistribution warranty is fabricated.

## Approval checkpoint

Review the concrete inventory and THIRD_PARTY_MATERIALS.md, then approve either (a) public publication of this complete-source proposal with the documented media exclusions and privacy redactions, or (b) continued hold pending the missing rights evidence. No public action happens before explicit approval. A future publication must verify the actual repository and uploaded tree against this approved inventory, then return its real URL and commit SHA.
