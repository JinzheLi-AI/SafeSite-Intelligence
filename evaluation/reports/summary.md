## Current OpenAI Sol pilot attempt - 2026-09-17

The 20-image manually reviewed pilot passed validation (20 ready, zero duplicates/errors). The run stopped after four consecutive connection_error failures, with zero successful inference results and 16 unattempted cases. No HTTP response, actual model, token usage or cost was returned. Requested model: gpt-5.6-sol; unchanged production prompt: vision-v1. No retries or DeepSeek calls occurred.

All vision precision/recall/F1, exact-match, safe-scene and review accuracy metrics remain unavailable. This is not a completed benchmark or evidence for a vision-accuracy competition claim. Primary manual review only; no secondary adjudication. Ground truth, images, product code and prompts remain unchanged. Earlier dataset-gate descriptions below are historical; the dataset is now ready and connectivity is the current blocker.

See [pilot report](vision_openai_sol_20/summary.md) for the full attempt report, per-case failures, usage availability and next steps. Previous RAG, policy and workflow measurements below are preserved and were not rerun.

---

# SafeSite Evaluation

No live vision accuracy or integrated ablation superiority is claimed. Ratios are 0-1.

## Hazard Recognition

PENDING LIVE EVALUATION

| Baseline | Precision | Recall | Micro F1 | Macro F1 |
| --- | ---: | ---: | ---: | ---: |
| Generic direct / SafeSite | Pending live evaluation | Pending | Pending | Pending |

## Regulation Retrieval

VERIFIED RESULT

Draft source-family relevance judgments on the existing pilot corpus; not a held-out expert benchmark.

| Baseline | Recall@1 | Recall@3 | Precision@3 | MRR | No-answer accuracy | Unsupported citations | Verified sources |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_only | 0.6389 | 0.7500 | 0.5833 | 0.6944 | 0.0000 | 0.0000 | 1.0000 |
| semantic_metadata | 0.7500 | 0.8333 | 0.7407 | 0.7917 | 0.2500 | 0.0000 | 1.0000 |
| safesite | 0.6944 | 0.8889 | 0.5185 | 0.7824 | 0.9167 | 0.0000 | 1.0000 |

## Risk Evaluation

VERIFIED RESULT - deterministic specification conformance.

| Metric | Value |
| --- | ---: |
| classification_accuracy | 1.0000 |
| boundary_accuracy | 1.0000 |
| override_accuracy | 1.0000 |
| human_review_accuracy | 1.0000 |
| score_accuracy | 1.0000 |

## Workflow Evaluation

MOCKED/UNIT-TEST RESULT - isolated database, injected AI.

| Metric | Value | Eligible scenarios |
| --- | ---: | ---: |
| workflow_success_rate | 1.0000 | 20 |
| safety_guardrail | 1.0000 | 14 |
| human_control | 1.0000 | 11 |
| audit_completeness | 1.0000 | 5 |
| state_transition | 1.0000 | 16 |

## Ablations

Component comparisons are measured separately. All A-D integrated scores remain pending; no workflow-control result is attributed to a generic LLM.

See summary.json and individual result files for case-level outcomes, errors, hashes and denominators.


## OpenAI Sol formal vision dataset gate ? 2026-09-17

**Blocked before paid execution: 0 human-reviewed images.** The audit found 4 distinct valid JPEG files, all unlabeled, and 72 placeholder manifest slots. All 4 files pass existing preprocessing. Filenames and previous model outputs were not used as ground truth. No human-reviewed safe, ambiguous or multi-hazard counts can be established; verified counts are zero and actual scene classifications remain unknown.

Configured target: openai / gpt-5.6-sol, production prompt vision-v1. The key is present without disclosure; current billing was not checked because the dataset gate failed. **0 new API calls**, no provider attempts or failures, and no new measured tokens, latency, cost or vision accuracy. No DeepSeek calls were made. Previous smoke usage is excluded from this benchmark.

Micro precision/recall/F1, macro F1, every per-class F1, safe-scene false-positive rate, ambiguous review recall, multi-hazard exact match and confidence statistics are **unavailable**, not zero. No benchmark false positives or negatives can be enumerated without human ground truth. Prior PPE concerns remain qualitative smoke observations, not scored errors.

Provide at least 20 independently reviewed real images (preferably 30?50). Review the existing four and add at least 16 more if all four are eligible; the preferred range requires 26?46 additional images. Labels must cover supported categories, safe negatives, ambiguity and multi-hazard scenes, with appropriate rights/provenance. See [the formal vision gate report](../../docs/VISION_BENCHMARK_OPENAI_SOL.md) for the precise record fields and remaining execution requirements. Audit hashes: [openai_sol_dataset_audit.json](openai_sol_dataset_audit.json).

No product or benchmark tooling changed. Evaluation tests: **34 passed**, with existing dependency deprecation warnings. Earlier measured results below/above retain their original dates and evidence; this update does not rerun or reclassify them.
