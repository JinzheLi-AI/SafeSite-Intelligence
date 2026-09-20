# Vision V2 implementation and evaluation plan

Status: implemented, opt-in, offline-tested; no measured accuracy improvement claimed.

## Design and compatibility

Vision-v1 remains the default. Its prompt source in app/ai/prompts.py is unchanged, and the v1 review branch retains its original behavior. The new prompt lives in app/ai/vision_v2.py. Configuration selects it with SAFESITE_VISION_PROMPT_VERSION=vision-v2; no .env file was modified. Select vision-v1 to use the original path. Reinspection retains reinspection-vision-v1 and its unchanged prompt/closure controls. Model/provider configuration is unchanged.

Vision-v2 requires supported evidence before emitting a positive class: absent AND contextually required PPE; credible elevated activity distinguished from uncontrolled fall exposure; visibly inadequate edge protection; a specific scaffold defect; a visible unsafe electrical condition; or a clear housekeeping mechanism. An unresolved possibility belongs in reasoning notes with uncertainty, not automatically in hazards. Empty hazard lists remain valid. Because this interface supplies only an image, it does not pretend to receive authenticated site requirements.

The model's existing structured requires_human_review field is explicitly instructed to mean uncertainty in the V2 prompt. The normalized InspectionAnalysis adds:

- model_uncertainty_review: model request/ambiguity, existing overall or individual confidence <0.85, or missing concrete evidence.
- operational_human_confirmation: true for any detected finding; calculated by the application, never entrusted to the model.
- requires_human_review: backward-compatible conservative aggregate. Either new signal keeps it true. Contract validation reasserts operational confirmation for hazards and uncertainty for low confidence/missing evidence. Neither field authorizes incident confirmation or closure.

V1 and old stored payloads omit these signals and parse with null values: unknown is not falsely represented as no review. Serialized payloads include additive nullable fields. Both split fields must be supplied together when used. Existing summary/hazards/confidence/requires_human_review/provenance fields remain. The workflow already stores analysis_json and revalidates InspectionAnalysis, so the fields survive persistence without a database migration. Existing consumers continue using the aggregate. Clients that reject any unknown JSON property need an additive-schema update; repository consumers/tests are checked, not every external client.

V2 does not use the v1 free-text keyword and PPE/height token matching as uncertainty gates; generic negated language and synonyms no longer trigger those lexical heuristics. Structured ambiguity/flags, evidence presence and existing numeric thresholds remain. The v1 checker is untouched. Mandatory incident confirmation remains unchanged and still requires an explicit human workflow action. RiskEngine still recalculates all scores from primitive factors. The elevated-activity definition does not change its policy overrides; therefore activity-only predictions may still receive conservative policy risk. This is a disclosed semantic limitation, not a reason to silently change RiskEngine.

## Tests and limits of offline evidence

Synthetic mocked responses cover hidden PPE, visible required-PPE absence, unknown requirement, empty safe scene, guarded elevated activity, scaffold without defects, electrical equipment without visible danger, clear housekeeping, and ambiguous scenes. Tests verify prompt selection/provenance, split review semantics, low-confidence/empty-evidence guards, old payload compatibility and actual API workflow persistence/confirmation with injected inference.

These fixtures test plumbing and contract behavior, not whether a real model correctly reads a photograph. No semantic parser can establish PPE necessity from arbitrary model prose here. A model may still violate the new prompt; the unchanged strict structured schema validates types, not photographic truth. Do not describe passing mocks as demonstrated precision improvement.

The historical dataset, model predictions and reports are not updated or rescored. Case_007 remains an unresolved PPE-requirement label ambiguity, not a confirmed model error. No complete relabeling exercise is requested from the user. Any later targeted adjudication is optional separate work and cannot establish independent test accuracy on reused images.

## Separate future evaluation plan

1. **Prepare new data, offline first.** A facilitator sources new authorized construction images disjoint from the historical 20 and smoke images. Create new manifests rather than editing vision_pilot_20.json. Group by site/session/source sequence and remove exact and near duplicates across splits. Do not infer labels from filenames.
2. **Development split:** proposed initial target 30-40 new images, with examples and counterexamples for all six classes, PPE task-requirement uncertainty, protected elevated activity and ordinary electrical equipment. This split alone may be used for future prompt iteration. Log all revisions and data exposure. Counts are collection targets, not assertions that data exists.
3. **Held-out split:** target at least 60 additional images from different sites/sessions, including at least 10 positive examples per class where feasible (multi-label overlap allowed), at least 15 supported empty scenes and at least 15 adjudication-needed scenes. Include electrical positives explicitly. If coverage is not achievable, report the gap and do not claim full-class validation.
4. **Consistent labels:** approve the proposed V2 protocol before inference. Qualified reviewers independently label new images without predictions, then reconcile disagreements; record requirement provenance, positive/negative/indeterminate states, uncertainty, adjudication need and operational confirmation separately. Context-only labels cannot fairly score an image-only model; exclude/report those targets separately. Freeze hashes and retain unresolved targets with explicit eligibility masks.
5. **Freeze before final comparison:** lock prompt bytes, code version, common image preprocessing, model, schema and policy. On later explicit authorization, run V1 and V2 once each per eligible held-out image with the same inputs and request policy. Do not mix historical V1 scores with a new V2 dataset. The elevated-activity definition differs from some historical labels; apply one prespecified label definition to both systems and disclose the semantic difference.
6. **Analysis:** report micro/per-class precision/recall/F1, exact match, empty-scene false positives, class coverage and confidence intervals, provider failures, usage and latency. Score uncertainty review separately from operational confirmation. Keep the legacy aggregate metric for compatibility but do not call it pure uncertainty. Predeclare handling of indeterminate cases and report denominators. Do not tune on final results or claim a gain before measured evidence exists.

**Exact next step:** create the new, site-separated development and held-out manifest templates and a collection checklist under a separate authorized data-preparation task. Collect and label the new material; do not rerun the historical 20 or launch paid calls now. Existing manual reviews are preserved and need not be repeated.

## Verification result

Full backend plus evaluation suites: **377 passed**, two existing dependency deprecation warnings, 106.17 seconds. This includes existing V1/provider/workflow regressions and 15 new V2 test cases. The initial targeted pass exposed one new test's incorrect expected confirmation status (corrected to the existing 201) and an older working-directory assumption; neither required product behavior changes.

The final test process imported settings from the repository root, disabled dotenv loading in memory, then changed to backend for cwd-sensitive tests. The existing backend autouse fixture blocks external HTTPTransport calls; model responses were injected mocks and fixtures. Production .env was neither loaded by that test bootstrap nor edited. Zero OpenAI/DeepSeek/paid inference calls occurred. Local TestClient requests exercised the application without external services.

Reproducible offline invocation from safesite:

```powershell
@'
import sys, os
from pathlib import Path
root = Path.cwd()
sys.path[:0] = [str(root / 'backend'), str(root)]
from app.core.config import Settings
Settings.model_config['env_file'] = None
import pytest
os.chdir(root / 'backend')
raise SystemExit(pytest.main(['tests', '../evaluation/tests', '-q']))
'@ | backend/.venv/Scripts/python.exe
```

Changed files: backend/app/ai/vision_v2.py (new prompt and uncertainty normalization); backend/app/ai/real.py (version selection and V2 normalization); backend/app/core/config.py (opt-in version setting); backend/app/schemas/contracts.py (additive signals and guardrails); backend/tests/test_vision_v2.py (offline tests); docs/VISION_V2_IMPLEMENTATION.md (this design and future evaluation plan). No workflow, RiskEngine, RAG, frontend, historical report or ground-truth changes.
