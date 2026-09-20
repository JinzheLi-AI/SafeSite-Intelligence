# SafeSite Evaluation - competition summary template

**Run ID/date:** [reference frozen summary.json]
**Data provenance:** [reviewed real images / draft queries / deterministic cases / injected workflow]

| Area | Metric | Value and status |
| --- | --- | --- |
| Hazard recognition | Precision / Recall / micro F1 / macro F1 | Pending live evaluation |
| Hazard recognition | Ambiguous review / obvious uncertainty rate | Pending live evaluation |
| Regulation retrieval | Recall@3 / MRR / Precision@3 | Copy from measured run; identify draft vs independently reviewed judgments |
| Grounding | Unsupported citation rate | Copy from measured run; include total citations |
| RiskEngine | Policy override / boundary correctness | Copy deterministic results; not field accuracy |
| End-to-end workflow | Scenario success rate | Copy result, explicitly MOCKED/UNIT-TEST RESULT |
| Human control | Closure guardrail success | Report scenario denominator and injected-provider status |
| Integrated A-D comparison | End-to-end improvement | Pending matched live evaluation |

Include all baseline outcomes, even where SafeSite performs worse. Do not call fixture-based workflow tests model accuracy, or source-family matches proof of legally applicable guidance. Supply dataset/corpus/prompt/model identifiers, case counts, errors and limitations with the slide or submission.
