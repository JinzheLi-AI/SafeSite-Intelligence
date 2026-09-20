# Real multimodal integration report

## Result
The existing SafetyAIProvider abstraction now supports mock and real image analysis, including real reinspection. No new pages, RAG, authentication, hazard categories or database migrations were added. Mock remains the default; real mode never falls back to mock.

## Provider selection and configuration
From the backend working directory, copy .env.example to .env if it does not already exist, then set:

```dotenv
SAFESITE_AI_PROVIDER=real
OPENAI_API_KEY=your-own-key
SAFESITE_VISION_MODEL=gpt-5.6-terra
SAFESITE_AI_TIMEOUT_SECONDS=90
SAFESITE_AI_MAX_OUTPUT_TOKENS=6000
```

Restart the backend after changing configuration. Keep the key on the backend only. Environment variables take precedence over .env. SAFESITE_AI_PROVIDER takes precedence over the legacy AI_PROVIDER alias. Set SAFESITE_AI_PROVIDER=mock for the unchanged offline scenario; no key is needed. The model can be changed to an accessible OpenAI model supporting image input and strict structured outputs. Missing credentials produce a clear health warning and a persisted failed execution if analysis is called; invalid credentials, unavailable models and quota failures are also explicit.

The installed official OpenAI Python SDK is 2.54.0, pinned with its dependencies in requirements.lock.txt. The dependency range is openai>=2.54,<3.

## Image-to-model path
The existing multipart upload endpoint validates decoded JPEG/PNG/WebP content, rejects unsupported formats, enforces a 10 MB default limit and a 25 megapixel limit, corrects EXIF orientation, strips metadata and re-encodes JPEG at quality 90 under a UUID filename. No spatial resizing is added. The encoded result must also fit the size limit.

The real provider resolves only files inside the configured upload directory, rejects traversal and unsafe paths, revalidates content and creates an input_image data URL containing the actual stored image bytes. It sends that image at detail=high to the official Responses endpoint. Filenames, inspection location and user description are not used as visual evidence or sent to the initial vision model. Reinspection sends original hazard context, original image when available, and the new rectification image. User claims that repairs are complete are not substituted for visual evidence. Requests set store=false; the application logs token counts when returned, not image content.

## Structured output
OpenAI responses.parse(text_format=VisualInspectionOutput) converts Pydantic contracts to strict JSON Schema. Parsed results are revalidated. Additional properties are forbidden, so model-supplied risk scores, risk labels, citations and incident status cannot enter this contract.

VisualInspectionOutput has:
- summary: nonempty string
- hazards: zero to 30 VisualHazardCandidate objects
- overall_confidence: strict numeric value from 0 to 1
- requires_human_review and ambiguity_detected: strict booleans
- reasoning_notes: up to 30 brief observation/limitation strings

Each candidate has:
- hazard_type: exactly one of missing_ppe, working_at_height, unprotected_edge, unsafe_scaffolding, electrical_hazard, housekeeping
- title and description
- visual_evidence: concrete observation strings; an empty list is retained but flagged
- confidence: strict numeric value from 0 to 1
- severity and exposure: strict integers 1 to 5
- probability: strict integer 1 to 4
- recommended_actions: 1 to 10 strings
- regulation_queries: up to 10 generic search queries

Malformed, incomplete or empty output is retried once, then fails without saved findings. Refusals and API/network errors are reported explicitly. SDK transport retries are disabled. No silent demo fallback exists.

## Versioned prompts
backend/app/ai/prompts.py contains vision-v1 and reinspection-vision-v1. The prompts restrict categories, allow zero hazards, require image-grounded observations, distinguish uncertainty from absence, avoid inferred height without supporting context, reject image-text instructions, and prohibit invented regulations/legal conclusions. Notes are brief evidence limitations, not chain-of-thought.

## Confidence and sanity checks
All nonempty findings retain the existing human-confirmation requirement, including high-confidence findings. Below 0.85, the analysis explicitly requires review; below 0.60, notes and the hazard panel mark evidence insufficient/uncertain. Low-confidence findings are retained and confidence does not reduce risk. Ambiguous or low-confidence zero-hazard assessments also require review.

Lightweight checks flag empty evidence, working-at-height evidence without height-related context, and missing-PPE claims without both an identifiable PPE item and absent/not-visible wording. These lexical checks flag review; they cannot verify that an observation is true in the image. The existing RiskEngine's legacy breakdown-level review flag remains unchanged; the stricter analysis-level review policy and human confirmation govern this integration.

## Risk and regulations
The provider adapts validated primitive factors into the existing InspectionAnalysis schema. The workflow independently recomputes final risk using the unchanged RiskEngine. Severity x exposure x probability, thresholds and WAH-001 remain authoritative. A working-at-height candidate with factors 5 x 4 x 1 has raw risk 20 and final risk 85/CRITICAL. The model never controls incident state or closure.

Real findings receive no seeded citation records. Their UI shows that verified regulation evidence is unavailable. Search queries remain in saved analysis JSON; they are not executed. Explicitly mock inspections retain labeled demo/unverified citations.

## Execution metadata and provenance
The existing AIExecution entity records workflow, entity association, provider=openai, configured model, prompt version, policy version, latency, status, confidence and sanitized failure message. Usage token counts are logged without a database redesign. Successful inspection/reinspection JSON also stores server-stamped provenance.

Results show REAL AI or DEMO AI, with model and prompt version. Historical records use successful execution metadata where available; records without provenance are labeled SOURCE UNKNOWN rather than guessed from filenames or current configuration.

## Real reinspection
Implemented behind the same abstraction with optional original_hazard context. The model returns whether the specific hazard remains present, mitigation confidence, evidence, same-location support, visual mitigation support, ambiguity and bounded current factors. The backend computes current risk and recommends KEEP_OPEN, HUMAN_REVIEW or ELIGIBLE_FOR_CLOSURE.

Eligibility requires no visible remaining hazard, confidence >=0.85, same-location and mitigation support, no ambiguity, an original image, and deterministic current risk below 25. Uncertain or mismatched images cannot produce eligibility. Even eligible results persist status REINSPECTION with closed_at=null. The existing explicit human Close Case command is still necessary.

## Verification
- Targeted provider tests: 59 passed, all offline.
- Full backend suite: 90 passed (31 existing + 59 new), run once after targeted tests.
- Frontend lint: passed, zero warnings.
- Typecheck: passed. An earlier overlapping build/typecheck encountered transient generated-file errors; sequential checks passed.
- Production build: passed, all existing routes generated.
- Browser verification: 6 passed (3 existing workflow/layout tests + 3 new offline real-mode UI tests). Zero-hazard and uncertain-result screenshots were visually reviewed. The offline fixtures are not live model evidence.
- No paid model calls occur in automated tests: external HTTPTransport is blocked by an autouse fixture; the SDK wire-format test uses httpx.MockTransport.
- Two existing dependency deprecation warnings remain in FastAPI/Starlette test-client integration; no test failures.

The targeted tests cover actual image-byte transport, official SDK strict-schema request formation, zero/multiple hazards, conservative review, sanity checks, invalid fields, one retry, refusal, empty/incomplete responses, timeout/network/auth/quota/model/API errors, sanitized failure persistence and retry, no fake citations, deterministic risk overrides, configuration, provenance and human-only closure.

## Live validation and limitations
No OPENAI_API_KEY was available. NO LIVE REAL-MODEL CALL WAS TESTED. Hazardous, relatively normal and ambiguous real-photo validation still requires credentials. Offline tests validate integration and controls, not recognition accuracy. Model access, model latency, cost, false positives, false negatives and calibration still need live evaluation.

No blocking regression was observed in tested flows. Remaining limits:
- The system is advisory and limited to six visual hazard categories.
- Lexical sanity checks cannot prove image-grounded correctness.
- Updated by the reliability follow-up: interrupted ANALYZING attempts can be retried on the same inspection after the stale window. See docs/LIVE_VISION_VALIDATION.md for attempt timestamps and late-response fencing. Ordinary handled provider errors restore CREATED.
- Real reinspection without an original image can return review only, never closure eligibility.
- The backend remains synchronous with local disk/SQLite storage, and the existing demo authentication limitations remain.
- Regulation retrieval is deliberately unfinished; no verified sources are synthesized.
- The frontend image picker uses the existing fixed 10 MB limit; backend MAX_UPLOAD_BYTES is configurable.
- JPEG re-encoding may lose fine detail; retain originals separately when needed for formal review.

## Exact click path for a new image
1. Configure backend real mode and your key, then restart the API from the backend directory.
2. Open http://127.0.0.1:3000/inspections (or Dashboard > New AI inspection).
3. Confirm the header says REAL AI provider and no configuration error appears.
4. Click New inspection if viewing an existing record.
5. Select project/site, enter location and upload a new JPEG, PNG or WebP construction image.
6. Click Analyze Site. Wait for validated visual observations.
7. Check Analysis source: REAL AI, model, confidence, evidence, uncertainty, risk breakdown and actions. Zero hazards is valid and has no Confirm Findings button; it does not establish the site is safe.
8. For supported findings, review and click Confirm Findings, then Open primary incident.
9. Start Rectification, verify and complete every corrective action, upload a new rectification image and click Run Reinspection.
10. Review the evidence. If eligible, click Close Case yourself; AI cannot do this automatically.
11. Repeat initial inspection with a normal image and an ambiguous image to complete live A/B/C validation. On a provider error, use Run saved inspection analysis to retry the saved image.

## Exact changed files
- `backend/app/core/config.py`
- `backend/app/ai/errors.py`
- `backend/app/ai/vision_contracts.py`
- `backend/app/ai/prompts.py`
- `backend/app/ai/images.py`
- `backend/app/ai/sanity.py`
- `backend/app/ai/real.py`
- `backend/.env.example`
- `backend/app/schemas/contracts.py`
- `backend/app/ai/provider.py`
- `backend/app/ai/mock.py`
- `backend/app/services/workflow.py`
- `backend/app/repositories/queries.py`
- `backend/app/api/overview.py`
- `backend/app/api/uploads.py`
- `backend/requirements.txt`
- `backend/requirements.lock.txt`
- `backend/tests/test_real_provider.py`
- `backend/tests/conftest.py`
- `frontend/src/lib/types.ts`
- `frontend/src/components/analysis-source.tsx`
- `frontend/src/components/inspection-results.tsx`
- `frontend/src/components/risk.tsx`
- `frontend/src/components/inspection-form.tsx`
- `frontend/src/app/inspections/page.tsx`
- `frontend/src/components/analysis-progress.tsx`
- `frontend/src/components/incident-detail.tsx`
- `frontend/src/components/image-upload.tsx`
- `frontend/src/components/reinspection-panel.tsx`
- `frontend/e2e/real-analysis.spec.ts`
- `README.md`
- `REAL_AI_IMPLEMENTATION.md`
