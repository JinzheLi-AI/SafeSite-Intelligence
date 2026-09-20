# Evaluation methodology

## Scope and status policy

This module evaluates the existing SafeSite implementation. It adds no product features and changes no RiskEngine, retrieval, SQL safety, provider or workflow behavior.

Each result has an explicit provenance status:

- **VERIFIED RESULT**: measured execution against real stored documents/local embeddings, or deterministic RiskEngine specification cases. This does not mean expert-validated generalization accuracy.
- **PENDING LIVE EVALUATION**: no scored real-image inference has occurred. Metrics are absent/null, not fabricated zeros. Integrated A-D ablations are also pending.
- **MOCKED/UNIT-TEST RESULT**: actual product workflow services run with isolated SQLite fixtures and injected AI. These numbers describe contract/guardrail conformance, never model accuracy.

The primary outputs are `evaluation/reports/summary.json` and `summary.md`, plus component JSON files and case-level records. Undefined denominators are null. The CLI exits nonzero for failed deterministic scenarios or scored inference/retrieval errors; intentional pending categories are permitted and clearly reported.

## Dataset composition and labeling

| Dataset | Current count | Ground truth status |
| --- | ---: | --- |
| hazards.json | 72 slots | No real images; all labels and ambiguity flags null |
| retrieval.json | 48 queries | 36 relevant source-family targets, 9 out-of-domain negatives, 3 unsupported-jurisdiction negatives; author-curated drafts |
| risk.json | 40 cases | Explicit expected policy outputs: 16 score boundaries and 24 assessments across six classes |
| workflow.json | 20 scenarios | Explicit success criteria mapped to unchanged integration-test nodes |

Hazard JSON fields include case_id, image_path, description, ground_truth_hazards, ambiguous, expected_human_review, notes and jurisdiction. Reviewed records additionally require an image SHA-256, group_id, two distinct reviewers, license/consent and label_status=reviewed. An empty label list means a reviewed negative scene; null means unlabelled and is never scored. The six allowed labels are the existing product hazard codes. Sampling-slot descriptions are recruitment targets, not observations.

Use the manual process in `evaluation/datasets/LABELING.md`. Two reviewers should label independently without seeing predictions, then adjudicate disagreements with a construction safety professional. Record ambiguity separately from mandatory human review. Group near-duplicate frames, locations and capture sessions; reserve entire groups for held-out evaluation. Freeze hashes and labels before any baseline results are inspected. Acquire diverse positive, negative, multi-hazard and ambiguous scenes; the 72 slots are not a validated distribution.

Retrieval labels use stable registry source keys/families rather than environment-dependent SQLite IDs. `expected_document_ids` accepts exact registry keys; `expected_source_families` accepts a base key and includes its addenda. Optional section keywords require at least one match in the section/excerpt in addition to the source match. Current family judgments are narrow, non-exhaustive and have not undergone independent passage-level review. Alternate relevant documents may therefore be scored as misses. These queries are developmental examples, not a held-out benchmark or proof of regulatory applicability.

## Hazard comparison and calibration

The optional live runner compares a generic direct image prompt against the actual SafeSite prompt, structured output and sanity checks. Both use the same configured model, actual image bytes, high image detail, English, structured schema, output-token limit and maximum two validation attempts. Baseline order alternates by case. The generic baseline has a shared output schema to permit scoring; it has no SafeSite hazard-specific prompt, sanity checks or policy postprocessing. This comparison does not separately isolate the benefit of structured formatting. The product provider is subclassed only for recording; product files are untouched.

Only reviewed images with matching hashes within image-root are sent. Filenames, ground truth and scene descriptions are not sent as visual evidence. Calls require `--live-vision` and configured backend credentials. No API key or raw image data is written to reports. Persisted outputs contain model, response IDs, token usage when supplied, prompt/image hashes, per-case errors, raw structured output and latency. Calls that fail remain in the denominator and cannot become successful empty scenes. Production model aliases and live sampling can vary over time; use an explicitly selected pinned model when available, repeat runs and report variability before claiming superiority.

Hazard scoring uses image-level sets (not boxes, instance counts or localization accuracy):

- Per class: TP, FP, FN, TN; precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN).
- Micro precision/recall/F1 pool the six labels. Macro F1 averages defined class F1 values; absent/unpredicted classes remain null rather than inflating the average.
- False-positive rate=FP/(FP+TN); false-negative rate=FN/(FN+TP). Exact match requires the complete predicted label set to equal the truth and a successful call.
- Completion rate and error count accompany accuracy. Failed calls contribute empty predictions for confusion counts, but never count as exact-match success. Negative-scene failures are thus visible in completion/exact-match even when they add only TN to label counts.
- Human-review agreement and ambiguous-case review rate measure review behavior. Obvious-case uncertainty rate is reported separately. All positive SafeSite findings require human review by design; that requirement must not be mislabeled as visual uncertainty.
- Generic uncertainty is model ambiguity or overall confidence below .85. SafeSite uncertainty additionally includes sanity flags. These are uncalibrated heuristics; uncertainty denominators are reported and failures excluded from uncertainty rates.

## Retrieval baselines and fairness

All three systems use the same operational vector index, model, expanded query and top-3 cap. The common index boundary excludes inactive/superseded documents and deliberately excluded chunks. The evaluation does not give the simpler baseline obsolete vectors merely to worsen its results.

1. **semantic_only**: cosine similarity over operational compatible vectors; no hazard, jurisdiction, verification, registry or effective-date filtering; no threshold or diversity rules.
2. **semantic_metadata**: same cosine scoring plus the actual product metadata requirements: project jurisdiction, verified sources, active documents/chunks, model signature, hazard tags, effective dates, registered URL/version/checksum and required addenda. No evidence threshold or reranking/diversity rules.
3. **safesite**: calls the unchanged production search function, including its lexical/specificity reranking, penalties, thresholds and diversity rules.

Hazard query expansion is identical for all systems. Query vectors are cached by text for fair reuse. Metadata eligibility in the baseline is evaluation-only and is tested against fixture behavior; maintain parity if the production filter changes. Rankings use deterministic chunk-ID tie breaking. Baseline results are independent objects, and isolation tests verify that changing one result cannot alter another.

Metrics: Recall@K is the fraction of judged document/family relevance units reached in the first K citations (duplicates count once); Hit@K reports whether any target is reached. Precision@3 counts relevant citations divided by 3, so abstention and fewer than three results reduce this measure. MRR uses the first relevant rank among returned top-3 citations. These metrics use answerable queries only. No-answer accuracy uses negative queries only; infrastructure errors are not successful abstentions. Deliberate unsupported-jurisdiction unavailability is a valid no-answer.

Unsupported citation rate counts returned citations failing exact stored chunk/document matching (relationship, title, excerpt, section, URL and checksum). It is distinct from semantic relevance. Verified-source rate requires verified, active source and active chunk. An irrelevant but correctly stored citation is not fabricated. All baselines in this clean pilot corpus may have 0% unsupported and 100% verified-source rates; those observations alone do not establish a comparative advantage. Zero returned citations produces null, not a claimed 0% fabrication rate.

No labels, thresholds or production ranking weights are tuned after observing this dataset's scores. A separate held-out, independently judged set is required for a competition accuracy claim. Threshold tuning should use a different development split and report recall/abstention tradeoffs.

## Risk and workflow

Risk cases are independently specified data, not expected values generated by calling RiskEngine. They cover LOW/MEDIUM/HIGH/CRITICAL boundary classification, WAH-001 trigger/non-trigger conditions, confidence .79/.80 and low confidence without risk discounting. Scores are deterministic policy conformance, not proof that severity/exposure/probability estimated from images are accurate.

Workflow evaluation reuses 20 existing scenario tests rather than implementing a second state machine. The runner executes them in a subprocess and parses JUnit results. Every test uses temporary databases and mocked/injected providers; the evaluation never calls a live app to create incidents. Scenarios include multi-hazard confirmation, rejection, rectification, eligibility, human-only closure, low confidence, failed provider retry, stale recovery, fresh-attempt protection, no evidence and zero hazards.

A scenario passes only if its selected test passes all assertions. Missing, skipped, errored or failed tests are failures. Axis metrics use only scenarios explicitly checking that axis; passing a retrieval test cannot imply audit completeness. Audit completeness means the prescribed events asserted by the five audit scenarios exist, not that every possible audit field/event has been proven complete. Metrics are correlated across scenarios and are not independent statistical samples. Human-control enforcement is workflow/actor-contract behavior, not authentication (none is added).

## Ablation interpretation

A-D system configurations are included in machine-readable results. Measured component metrics can be inspected alongside their configuration. No integrated score is computed by multiplying component accuracies or assuming an unimplemented generic LLM supports closure controls. A and B have no measured human-control capability. Full integrated vision-to-workflow comparison remains pending real labeled images, shared recorded predictions and matched downstream scenarios. The current executable ablations are the paired vision adapter, the three retrieval runs, and the independent policy/workflow checks.

## Reproducibility and commands

From the `safesite` directory in PowerShell, using the existing backend environment:

```powershell
backend/.venv/Scripts/python.exe evaluation/run.py
backend/.venv/Scripts/python.exe -m pytest evaluation/tests -q
```

The runner resolves paths before changing to backend for existing settings. It reads the local product database in read-only mode, creates a consistent temporary backup, queries it read-only and removes the backup. Reports retain corpus/source-registry fingerprints, dataset hashes, product/evaluation/test code hashes, dependency versions, embedding signature, thresholds and per-case outcomes. Historical stored revisions are fingerprinted but are not baseline candidates. The local fastembed cache is used with downloads disabled. No remote embeddings or model calls occur in the default command. A missing local corpus or model is reported explicitly; embedding errors are not replaced by mock scores.

To keep separate reproducible runs:

```powershell
backend/.venv/Scripts/python.exe evaluation/run.py --output evaluation/reports/run-02
```

For reviewed images and authorized paid inference, set the backend API key securely (never in a manifest/report), select the model through existing settings, and run:

```powershell
backend/.venv/Scripts/python.exe evaluation/run.py --datasets evaluation/datasets --image-root evaluation/datasets --live-vision --max-vision-cases 100 --output evaluation/reports/live-01
```

Maximum cost exposure is two systems times up to two structured-output validation attempts per selected image, plus the existing per-call token limit. No credentials or images are currently available; default reports show pending model accuracy. To reproduce scores, preserve the exact frozen dataset, corpus and local model cache. Regenerating a live run does not guarantee identical stochastic outputs.

Full regression commands:

```powershell
Push-Location backend
.venv/Scripts/python.exe -m pytest -q
Pop-Location
Push-Location frontend
& D:/nodejs/npm.cmd run lint
& D:/nodejs/npm.cmd run typecheck
& D:/nodejs/npm.cmd run build
& D:/nodejs/npm.cmd run test:e2e
Pop-Location
```

Browser tests require the existing local API at port 8000 and production frontend at port 3000. Those existing browser regressions create demo records; evaluation workflow scenarios themselves use isolated databases. Matplotlib is not installed, so the framework uses lightweight JSON and Markdown tables without adding visualization dependencies.

The optional provider adapter follows the existing repository SDK pattern and the [official structured outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Structured formatting alone does not establish observational accuracy.
