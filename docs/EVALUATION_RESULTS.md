## Current OpenAI Sol pilot attempt - 2026-09-17

The 20-image manually reviewed pilot passed validation (20 ready, zero duplicates/errors). The run stopped after four consecutive connection_error failures, with zero successful inference results and 16 unattempted cases. No HTTP response, actual model, token usage or cost was returned. Requested model: gpt-5.6-sol; unchanged production prompt: vision-v1. No retries or DeepSeek calls occurred.

All vision precision/recall/F1, exact-match, safe-scene and review accuracy metrics remain unavailable. This is not a completed benchmark or evidence for a vision-accuracy competition claim. Primary manual review only; no secondary adjudication. Ground truth, images, product code and prompts remain unchanged. Earlier dataset-gate descriptions below are historical; the dataset is now ready and connectivity is the current blocker.

See [pilot report](../evaluation/reports/vision_openai_sol_20/summary.md) for the full attempt report, per-case failures, usage availability and next steps. Previous RAG, policy and workflow measurements below are preserved and were not rerun.

---

# Evaluation results

Evaluated on 2026-09-15 against the existing local SafeSite project. Product behavior and all existing test assertions are unchanged.

## Result status and dataset size

| Area | Cases | Status | Meaning |
| --- | ---: | --- | --- |
| Hazard recognition | 72 slots, 0 reviewed images, 0 model calls | PENDING LIVE EVALUATION | No precision, recall or F1 claim |
| Regulation retrieval | 48 draft queries | VERIFIED RESULT | Actual stored pilot corpus and local fastembed execution; labels are not an independently reviewed benchmark |
| Risk / policy | 40 deterministic cases | VERIFIED RESULT | Conformance to the declared policy, not field hazard accuracy |
| End-to-end workflow | 20 scenarios | MOCKED/UNIT-TEST RESULT | Actual services and isolated databases with injected AI |
| Integrated A-D ablations | 4 configurations | PENDING LIVE EVALUATION | No fabricated combined score or superiority claim |

## Measured retrieval comparison

The same operational 383-vector index and query expansion were used for all three systems. Superseded/excluded vectors were not handed to the simpler baseline to make it look worse. The local database contains historical revisions; only 9 current source documents participate in the pilot index.

| System | Recall@1 | Recall@3 | Precision@3 | MRR | No-answer accuracy | Unsupported citation rate | Verified-source rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Semantic only | 63.89% | 75.00% | 58.33% | 0.6944 | 0.00% | 0.00% | 100.00% |
| Semantic + metadata | 75.00% | 83.33% | 74.07% | 0.7917 | 25.00% | 0.00% | 100.00% |
| SafeSite production retrieval | 69.44% | 88.89% | 51.85% | 0.7824 | 91.67% | 0.00% | 100.00% |

SafeSite reached the declared target source family for 32/36 answerable queries within the top three and abstained on 11/12 no-answer queries. Its Recall@3 and no-answer accuracy were higher on this draft set, while metadata-only retrieval had higher top-1 recall, Precision@3 and MRR. Precision@3 divides by three even when the threshold returns fewer citations, so selective abstention has a cost in this metric. No weights, thresholds or labels were adjusted to optimize these scores.

All three baselines returned stored, currently verified source text. The 0% unsupported-citation observation therefore does not distinguish their performance on this clean corpus. It measures grounding, not relevance or legal applicability. Draft source-family targets are non-exhaustive, so alternative useful sources may be penalized. Broad out-of-domain negatives are easier than near-domain hard negatives. No statistical significance or generalization claim is made.

The case-level JSON identifies misses, the negative query receiving evidence, returned chunks and source text, and infrastructure errors. Dataset, source registry, corpus, code, model signature and dependency fingerprints accompany the result.

## Risk and workflow

All 40 risk cases match their expected classification. All 16 boundary cases and 24 assessment cases pass; the assessment cases also pass score, override and confidence-driven review checks. These expectations are explicit fixture data, not generated from RiskEngine outputs.

All 20 workflow scenarios pass. Axis denominators are 14 safety-guardrail scenarios, 11 human-control scenarios, 5 prescribed-audit scenarios and 16 state-transition scenarios. These are overlapping assertions against mocked/injected inference, not 20 real construction inspections. In particular, the human closure test rejects AI actor requests and confirms that reinspection eligibility does not itself close the case. Audit completeness is restricted to the expected events asserted by the selected scenarios.

## Regression results

| Check | Result |
| --- | --- |
| Existing product backend suite | 229 passed |
| Evaluation framework suite | 27 passed |
| Evaluation workflow subprocess | 20 passed |
| Existing browser suite | 19 passed, 36.9 seconds |
| Frontend lint | Passed |
| Frontend standalone typecheck | Passed |
| Frontend production build | Passed |

The 20 workflow selections are a reused subset of product tests, not 20 new independent tests. Backend/evaluation output includes existing dependency deprecation warnings. No new dependency was installed. Matplotlib is unavailable; reports use Markdown tables and JSON.

## Files and rerun instructions

- Main entry: `evaluation/run.py`.
- Strict hazard/retrieval records: `evaluation/schema.py`; scoring: `evaluation/metrics.py`.
- Adapters: `evaluation/runners/{vision,retrieval,risk,workflow}.py`.
- JSON manifests and manual labeling instructions: `evaluation/datasets/`.
- Artificial metric fixture only: `evaluation/fixtures/hazard_scoring.json`.
- Machine-readable component results, full summary and workflow execution evidence: `evaluation/reports/`.
- Competition-ready template: `evaluation/COMPETITION_SUMMARY_TEMPLATE.md`.

From `safesite`:

```powershell
backend/.venv/Scripts/python.exe evaluation/run.py
backend/.venv/Scripts/python.exe -m pytest evaluation/tests -q
```

For the complete baseline definitions, metric denominators, live-call command, labeling procedure and reproduction limits, see [methodology](EVALUATION_METHODOLOGY.md). Generated [summary](../evaluation/reports/summary.md) and [machine-readable results](../evaluation/reports/summary.json) are the authoritative run outputs.

## What is needed next

Provide 60-100 approved real photographs with independent, adjudicated six-category labels, ambiguity flags, review expectations, image hashes and source/consent provenance. Reserve held-out groups by site/session. Independently review the retrieval queries and judge relevant passages/families, including near-domain hard negatives. Then configure authorized API credentials and a chosen vision model and use the explicit paired live command in the methodology. Keep both successful and failed calls and repeated-run variability; do not replace missing results with mock accuracy.

## Exact files created or changed

The inventory below excludes runtime caches, databases and browser-generated artifacts. No file under `backend/app`, `backend/tests`, `frontend/src` or `frontend/e2e` changed for this evaluation task.

- `README.md`
- `docs/EVALUATION_METHODOLOGY.md`
- `docs/EVALUATION_RESULTS.md`
- `evaluation/COMPETITION_SUMMARY_TEMPLATE.md`
- `evaluation/__init__.py`
- `evaluation/datasets/LABELING.md`
- `evaluation/datasets/hazards.json`
- `evaluation/datasets/retrieval.json`
- `evaluation/datasets/risk.json`
- `evaluation/datasets/workflow.json`
- `evaluation/fixtures/hazard_scoring.json`
- `evaluation/metrics.py`
- `evaluation/report.py`
- `evaluation/reports/ablations.json`
- `evaluation/reports/hazard.json`
- `evaluation/reports/retrieval.json`
- `evaluation/reports/risk.json`
- `evaluation/reports/summary.json`
- `evaluation/reports/summary.md`
- `evaluation/reports/workflow-junit.xml`
- `evaluation/reports/workflow-pytest.txt`
- `evaluation/reports/workflow.json`
- `evaluation/run.py`
- `evaluation/runners/__init__.py`
- `evaluation/runners/retrieval.py`
- `evaluation/runners/risk.py`
- `evaluation/runners/vision.py`
- `evaluation/runners/workflow.py`
- `evaluation/schema.py`
- `evaluation/tests/conftest.py`
- `evaluation/tests/test_evaluation.py`
- `evaluation/tests/test_retrieval_integration.py`


## OpenAI Sol formal vision dataset gate ? 2026-09-17

**Blocked before paid execution: 0 human-reviewed images.** The audit found 4 distinct valid JPEG files, all unlabeled, and 72 placeholder manifest slots. All 4 files pass existing preprocessing. Filenames and previous model outputs were not used as ground truth. No human-reviewed safe, ambiguous or multi-hazard counts can be established; verified counts are zero and actual scene classifications remain unknown.

Configured target: openai / gpt-5.6-sol, production prompt vision-v1. The key is present without disclosure; current billing was not checked because the dataset gate failed. **0 new API calls**, no provider attempts or failures, and no new measured tokens, latency, cost or vision accuracy. No DeepSeek calls were made. Previous smoke usage is excluded from this benchmark.

Micro precision/recall/F1, macro F1, every per-class F1, safe-scene false-positive rate, ambiguous review recall, multi-hazard exact match and confidence statistics are **unavailable**, not zero. No benchmark false positives or negatives can be enumerated without human ground truth. Prior PPE concerns remain qualitative smoke observations, not scored errors.

Provide at least 20 independently reviewed real images (preferably 30?50). Review the existing four and add at least 16 more if all four are eligible; the preferred range requires 26?46 additional images. Labels must cover supported categories, safe negatives, ambiguity and multi-hazard scenes, with appropriate rights/provenance. See [the formal vision gate report](VISION_BENCHMARK_OPENAI_SOL.md) for the precise record fields and remaining execution requirements. Audit hashes: [openai_sol_dataset_audit.json](../evaluation/reports/openai_sol_dataset_audit.json).

No product or benchmark tooling changed. Evaluation tests: **34 passed**, with existing dependency deprecation warnings. Earlier measured results below/above retain their original dates and evidence; this update does not rerun or reclassify them.
