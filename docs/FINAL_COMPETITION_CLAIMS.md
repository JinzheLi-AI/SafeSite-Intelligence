# Competition evidence and claims

SafeSite is a local competition prototype with a human-controlled inspection-to-closure workflow. It is not production-ready or an independent safety authority.

Architecture: Next.js/TypeScript interface -> FastAPI -> provider interface, deterministic RiskEngine, regulatory retrieval and guarded workflow -> SQLite records, evidence files and audit history. Vision-v1 remains default; V2 is experimental. No additional agents or large features were added.

Implemented: validated upload, structured visual observations/provenance, risk factors and policy override, regulatory passage retrieval with stored-source grounding, explicit human confirmation, assigned corrective actions, reinspection, human-only closure, audit history, bilingual interface and deterministic database analyst. Live mode does not silently substitute mock predictions. No authentication/authorization is implemented; the displayed role is a demo identity.

| Evidence | Measured result | Honest interpretation |
|---|---|---|
| Historical V1 20-image pilot, evaluation/reports/vision_openai_sol_20_20260918_01 | Precision 48.28%, recall 93.33%, F1 63.64%; safe-scene FP 42.86% | Small pilot, single primary reviewer, AI-assisted annotation discussion, no secondary adjudication, reused smoke images, no electrical positives. Not independent validation. |
| Paired V1/V2 10-image development set, paired_live_20260919_step16 | V1 P/R/F1 41.18/100/58.33%; V2 41.67/71.43/52.63%; safe FP 100% -> 33.33%; FN 0 -> 2 | V2 is not superior overall. 59 determinate pairs; case 008 housekeeping masked; 9 exact-match cases; 3 safe scenes. Development tuning evidence only. |
| Historical local RAG evaluation, docs/EVALUATION_RESULTS.md | Production Recall@3 88.89%, no-answer accuracy 91.67%, 0% unsupported citations on 48 draft queries | Existing 9-document HK corpus, 383-vector index; actual local retrieval, draft/non-independent targets. Grounding is not legal applicability or field validity. Not rerun for Day 1. |
| Historical risk policy evaluation | 40/40 declared-policy cases | Policy conformance, not hazard-recognition accuracy. Day 1 backend risk boundary/override tests rerun. |
| Historical workflow evaluation | 20/20 selected scenarios with mocked AI | Service/DB safety controls tested, not real-site outcomes. Day 1 browser/API workflows additionally executed. |

Human safeguards: no incident before confirmation; action completion and evidence required before reinspection; AI cannot close incidents; eligible reinspection still needs explicit human closure; uncertainty does not certify safety; risk is not reduced merely because confidence is low. Citation forgery and absent-evidence paths are tested. Backend external HTTP is blocked in tests.

Day 1 live checks were DNS/TLS only (unauthenticated OpenAI endpoint returned 401). No new paid calls, no V2.1 and no additional benchmark. Existing reports are preserved even where older narrative says evaluation was pending; use dated completed-run evidence above for current claims rather than overwriting historical records.
