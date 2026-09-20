# OpenAI live vision smoke test

**Current status after the authorized preprocessing follow-up: the two-image OpenAI API compatibility smoke is complete. Two real requests total across both stages, one per image; no retries.** The safe-image request succeeded after preprocessing but returned an uncertain eye-protection candidate rather than zero hazards. This is a potential false positive, not an established PPE violation. Successful API/schema handling does not establish accuracy or satisfy a claim that no unsupported hazard was inferred. See the follow-up results at the end of this report. The initial-stage results below are preserved as historical evidence.

Initial run (historical): 2026-09-16, 23:02:10-23:02:29 Asia/Shanghai (15:02 UTC). **Partial smoke result: one successful real request; the other image was rejected locally before any request. This is not a formal accuracy benchmark.**

## Configuration and scope

Safely verified backend/.env contains SAFESITE_VISION_PROVIDER=openai, SAFESITE_VISION_MODEL=gpt-5.6-sol and SAFESITE_ANALYST_PROVIDER=deterministic. OPENAI_API_KEY is present; its value was never printed, serialized or logged. Git confirms backend/.env is ignored. The file's before/after hash matches; it was not edited.

A legacy setting, SAFESITE_AI_PROVIDER=openai, initially caused a local Settings validation error because the legacy field accepted only mock/real. The only product change accepts openai as an alias of real. Explicit workload selection still takes precedence. This fixes startup without modifying .env or routing to another provider. Regression coverage was added for the alias and explicit-provider precedence.

[Official OpenAI documentation for GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), checked 2026-09-16, lists image input, Responses and structured output support. Account-level compatibility was established by the successful HTTP 200 response described below, not inferred from documentation alone.

The one-shot evaluation runner uses the existing provider factory and exact RealMultimodalSafetyAIProvider implementation, original prompt vision-v1, original schema, normalization, sanity checks and RiskEngine. It reads only the two specified images. SDK retries are zero and validation attempts are one. A request hook enforces at most two requests overall and one per image; a durable execution lock prevents accidental reruns. No DeepSeek calls, full benchmark, database workflow calls, incident creation or incident closure occurred. The existing upload root is temporarily pointed at the fixture directory in the smoke process only; neither fixture is copied, resized nor re-encoded. This exercises the provider pipeline, not the upload HTTP endpoint or incident workflow.

## Image validation and results

| Item | Case A: 01_safe.jpg | Case B: 02_obvious_hazard.jpg |
| --- | --- | --- |
| File / decode check | Exists; valid JPEG | Exists; valid JPEG |
| Dimensions | 5118 x 7677, 39,290,886 pixels | 5614 x 3733, 20,957,062 pixels |
| File bytes | 2,178,623 | 2,417,773 |
| Pipeline outcome | Blocked by existing 25-megapixel guard | Success, HTTP 200 |
| Actual API requests | 0 | 1 |
| Requested provider/model | openai / gpt-5.6-sol | openai / gpt-5.6-sol |
| API-returned model | Not applicable | gpt-5.6-sol |
| Prompt version | vision-v1 configured; not sent | vision-v1 sent and recorded |
| Detected hazard types | Not assessed; no prediction | missing_ppe, tentative eye-protection concern |
| Overall confidence | Not available | 0.78 |
| Hazard confidence | Not available | 0.74 |
| Human review | Not assessed | Required |
| Final risk | Not assessed | 18 / 100, LOW |
| Input tokens | null; no call | 3,861 |
| Output tokens | null; no call | 643 |
| Total tokens | null; no call | 4,504 |
| Call latency | Not applicable | 18,886 ms |
| Estimated USD cost | Not applicable; no call | null; no applicable pricing configured |

### Case A: local size rejection

The original JPEG is valid, but exceeds the existing 25,000,000-pixel limit in the real provider image loader (and upload API). Error code: invalid_image. Message: "Use a valid JPEG, PNG or WebP image up to 25 megapixels."

No image bytes were sent to OpenAI for this case. Zero-hazard acceptance remains covered by offline provider tests but was **not verified live**. There is no live confidence, human-review result, hazard prediction or risk level for this image. Its filename is not a ground-truth label. The original image and the application's existing size guard were preserved; no preprocessing was silently introduced to make the test pass.

### Case B: successful real response

The outgoing HTTPS request hook verified that the single input_image data URL decoded to exactly the original fixture bytes and that the request targeted https://api.openai.com/v1/responses with model gpt-5.6-sol and store=false. The filename was absent from the API payload. The response returned HTTP 200 and model gpt-5.6-sol. Strict structured observations and the normalized InspectionAnalysis both validated successfully. No fallback occurred.

The model returned one candidate: **missing_ppe — Safety eyewear not visible during rebar work**. Its visual evidence was:

- Both foreground workers have gloved hands at the reinforcing-steel cage.
- No safety glasses or goggles are visible on the foreground workers.
- Downward head positions, helmet brims and the camera angle partly obscure their eye areas.

The response explicitly says PPE absence **cannot be confirmed from the image alone**. This is an uncertain candidate requiring human inspection, not a verified PPE violation. Recommended actions are to verify suitable eye protection and assess face-protection needs for the task. Visual review supports the described rebar work and limited eye visibility, but cannot establish whether suitable eyewear is actually absent. Treat the finding as a possible false positive until human review; this smoke test does not establish detection accuracy.

The model recognized visible hard hats, high-visibility vests and gloves. It noted projecting/bent rebar ends near the workers but did not invent a new category for exposed-rebar/impalement risk. It also did not infer an elevated work surface, open edge, unsafe scaffold or electrical source from an unclear background. These observations illustrate the fixed taxonomy's coverage limit; the supplied filename does not justify forcing a CRITICAL result.

The only returned enum, missing_ppe, belongs to the existing six: missing_ppe, working_at_height, unprotected_edge, unsafe_scaffolding, electrical_hazard and housekeeping. No categories were added. No purported regulation numbers, quotations or authoritative citations were generated; regulation_queries contains only search phrases. RAG was not executed or modified.

RiskEngine independently computed severity 3 x exposure 3 x probability 2 = **18, LOW**, policy safety-policy-1.0, with no override. Recalculation matched the normalized result. Confidence did not reduce the risk score. The model reported ambiguity, and the existing sanity checks retained human-review requirements and added uncertainty notes. LOW is the score of this candidate, not a declaration that the site is safe.

## Usage and cost

**Total actual requests: 1 of a maximum 2. No retries. Total reported usage: 3,861 input + 643 output = 4,504 tokens.** Case A incurred no API request; unavailable fields are null rather than fabricated token counts.

Per-call metadata is preserved in [results.json](../evaluation/reports/live_openai_smoke/results.json): workflow inspection-analysis, provider, requested/returned model, prompt version, status, confidence, latency, tokens and nullable cost. API-reported cached input tokens are 0; cache-write tokens are 3,858. The existing accounting module captured these directly. The empty pricing registry supplies no applicable verified rate, and the estimator does not support positive cache-write billing. **Estimated total monetary cost is unavailable (null), not $0.** No pricing entry was added and no charge was guessed from public headline rates. Provider billing remains authoritative.

The runner uses the existing AIExecution accounting attachment logic to form the records, but deliberately does not persist an operational database row or incident. Normalized analysis provenance is therefore not populated by the incident workflow; provider/model/prompt provenance is explicitly recorded in the smoke case and its actual call record.

## Errors and readiness

- Local configuration error: legacy openai spelling rejected before the targeted alias fix. No paid call was made at this stage.
- Local Case A error: exceeds 25-megapixel limit; no paid call.
- API errors for the one attempted request: **none**. No authentication, schema, model-access or service error occurred.
- Runtime API compatibility for Case B: verified.
- Both-image smoke goal: incomplete because Case A cannot traverse the unchanged input guard.
- Formal Vision Benchmark readiness: **not yet a complete go-ahead**. Prepare an independently reviewed, licensed dataset within existing image constraints, covering the six supported categories and safe/ambiguous controls. A user-authorized compliant safe image (or separately authorized preprocessing/limit change) is needed to finish the live safe-control check. Assess the uncertainty/false-positive behavior and the exposed-rebar taxonomy gap when selecting benchmark labels. No further calls were made or scheduled.

## Regression and file integrity

Only affected provider/config tests were run; no frontend, RAG or full benchmark suite was started. Existing tests initially picked up live workload settings from .env, causing three configuration-dependent failures; their external-HTTP guard prevented network requests. Re-running with isolated in-memory offline settings does not edit .env. Final result: **99 affected provider/config tests passed** (23.23 seconds), with only existing Starlette/httpx and AnyIO deprecation warnings. The exact pytest selection was tests/test_real_provider.py, tests/test_multi_provider.py and tests/test_live_smoke_config.py. No automated test made a paid request.

Original SHA-256 values, verified unchanged after the smoke:

- 01_safe.jpg: 7682ce9f5acadbefeb92264bbf1f7ba15c781c2e85e4d47370104a1644b2c72e
- 02_obvious_hazard.jpg: 51fe0ae6c2a7c41486af2785fd905db62607d4dcb8c90c47d6291d4d8ec59611

Files changed/created for this task:

- backend/app/core/config.py — minimal legacy openai alias compatibility fix.
- backend/tests/test_live_smoke_config.py — alias and explicit-provider precedence tests.
- evaluation/live_openai_smoke.py — one-shot bounded smoke harness.
- evaluation/reports/live_openai_smoke/results.json — actual sanitized results.
- evaluation/reports/live_openai_smoke/execution.lock — durable no-rerun marker.
- docs/LIVE_PROVIDER_SMOKE_TEST.md — this report.

RiskEngine, RAG, incident workflow, prompts, provider normalization, image-size guard, frontend and .env were not changed.


## Authorized oversized-image follow-up ? 2026-09-16

Only evaluation/fixtures/live_smoke/01_safe.jpg was submitted in this follow-up. The existing configured model gpt-5.6-sol and prompt vision-v1 were unchanged. The one-shot runner used --safe-only --execute with an independent durable lock, a one-request HTTP hook limit, SDK max_retries=0 and one validation attempt. No other image, DeepSeek request or full benchmark was run.

### Preprocessing implementation and integrity

The provider image loader and upload endpoint now share prepare_image, using the existing Pillow dependency. Both validate byte size and JPEG/PNG/WebP format, verify the container and fully decode it to detect truncated content. Pillow's decompression-bomb warnings/errors are rejected rather than disabled. Images above 25 MP are EXIF-transposed and resized with LANCZOS to a maximum 2400-pixel side while retaining aspect ratio. Processed images are encoded as high-quality JPEG (quality 95, no chroma subsampling), with a fresh RGB canvas to remove metadata. Transparency is flattened on white. The processed output must still pass the configured byte limit.

Correctly oriented provider images at or below 25 MP keep their exact original bytes. Nontrivial EXIF orientation is applied even on smaller images. Uploads retain their existing sanitizing re-encode and generated-filename storage behavior; preprocessing never overwrites the source fixture or client file. All direct-provider preprocessing takes place in memory. No RiskEngine, RAG, incident workflow, AI prompt, model or frontend change was made.

| Safe-image preprocessing | Verified result |
| --- | --- |
| Original dimensions | 5118 x 7677 (39,290,886 pixels) |
| Processed dimensions | 1600 x 2400 (3,840,000 pixels) |
| Aspect ratio | 2:3 before and after |
| Original bytes | 2,178,623 |
| Processed bytes | 954,120 |
| Original preserved | Yes; original SHA-256 unchanged |
| Original SHA-256 | 7682ce9f5acadbefeb92264bbf1f7ba15c781c2e85e4d47370104a1644b2c72e |
| Processed SHA-256 | 309c0a5720690a8492cbef62058ea1f45405873df5b009b947310d1bb58d23f3 |
| .env preserved | Yes; before/after hash unchanged |

The outgoing request hook decoded the actual input_image data URL and verified that it equaled the preprocessed bytes, not the original oversized bytes. The filename was not sent. The request targeted the official Responses endpoint with store=false, and the SDK returned gpt-5.6-sol. The original bytes were never overwritten. This resolves the earlier local rejection through processing, without simply removing the oversized-image threshold or disabling the independent unsafe-image protections.

### Safe-image API result

| Field | Actual result |
| --- | --- |
| API result | Success, HTTP 200 |
| Structured output | Valid original visual schema and normalized InspectionAnalysis |
| Provider / returned model | openai / gpt-5.6-sol |
| Prompt | vision-v1 |
| Zero hazards returned | **No** |
| Hazard type | missing_ppe |
| Candidate title | Eye protection not visibly worn |
| Overall confidence | 0.78 |
| Candidate confidence | 0.78 |
| Ambiguity | true |
| Human review | Required |
| Risk inputs | Severity 2, exposure 2, probability 2 |
| Final risk | **8 / 100, LOW**, computed by unchanged RiskEngine |
| Input tokens | 3,813 |
| Output tokens | 729 |
| Total tokens | 4,542 |
| Call latency | 15,879 ms |
| Provider operation elapsed | 16,449 ms, including local preprocessing/normalization |
| Cached input tokens | 0 |
| Cache-write tokens | 3,810 |
| Estimated USD cost | null; no applicable configured pricing |
| API error | None |
| Mock fallback | None |
| Additional real requests | **1** |

Actual visual evidence reported by the model:

- Both workers' faces and eyes are visible without eyewear being worn.
- A pair of clear glasses appears to hang from the clothing of the worker on the right.
- The workers appear to be reviewing a clipboard and handheld device rather than performing a visibly hazardous operation.

The model recognized the hard hats and one high-visibility vest. It stated that no airborne-particle, chemical or impact exposure was established, and explicitly acknowledged that eye protection might not be required for the visible activity. It found no supported working-at-height, edge, scaffold, electrical or housekeeping hazard. No authoritative regulation citation was invented; the only regulation-related output was search queries.

**Interpretation:** visible eyewear absence supports the observation, but does not establish that required PPE is missing. The missing_ppe candidate is therefore a possible false positive that needs human review. The model's category is one of the supported six, but supported taxonomy is not proof of a supported safety violation. The safe filename was neither sent nor used to force a zero-hazard prediction. No finding was suppressed to make the smoke appear successful. The criterion of ?no unsupported hazards? cannot be certified from this response. Zero-hazard output remains permitted and tested offline, but neither live case returned zero hazards.

The unchanged RiskEngine calculation was independently checked: 2 x 2 x 2 = 8, LOW, no overrides, safety-policy-1.0. Confidence did not discount that score. The model ambiguity and existing sanity checks kept human review enabled. LOW is the candidate's score, not a site-safety certification. No incidents or operational database rows were created or closed.

Raw sanitized evidence: [safe follow-up results.json](../evaluation/reports/live_openai_safe_preprocessed/results.json). Per-call records use the existing accounting attachment logic and contain actual usage, latency, model, prompt and confidence. Keys and request headers are absent. The empty pricing registry and unsupported positive cache-write billing mean no dollar cost is estimated. Null does not mean zero billing.

### Cumulative smoke outcome and regression

Across both stages: **2 successful real OpenAI requests total**, with no retries: one earlier hazard-image call and one safe-image follow-up call. Total reported usage is **7,674 input + 1,372 output = 9,046 tokens**. Estimated cumulative USD cost remains unavailable. No DeepSeek testing or formal benchmark was started.

**143 affected tests passed**, covering preprocessing, OpenAI/provider accounting, configuration and upload/workflow regressions. Focused tests cover oversized JPEG resize, unchanged normal JPEG/PNG/WebP bytes, aspect ratio, preservation of the original file, EXIF rotation, malformed and truncated inputs, retained byte/decompression limits, upload sanitization and exact processed bytes reaching an injected provider. Tests use isolated offline configuration and forbid external HTTP; no regression test incurs API charges. The existing two Starlette/httpx and AnyIO deprecation warnings remain.

Exact test selection: tests/test_image_preprocessing.py, tests/test_real_provider.py, tests/test_multi_provider.py, tests/test_live_smoke_config.py and tests/test_workflow.py. Product source did not change after this passing test run; the live invocation exercised that same code.

Changed/created in this follow-up:

- backend/app/ai/images.py ? shared validation and in-memory preprocessing.
- backend/app/api/uploads.py ? shared preprocessing, preserving upload sanitization and byte limits.
- backend/tests/test_image_preprocessing.py ? focused offline regression coverage.
- evaluation/live_openai_smoke.py ? bounded safe-only continuation, processed-byte verification and dimensions/hash recording.
- evaluation/reports/live_openai_safe_preprocessed/results.json ? actual follow-up result.
- evaluation/reports/live_openai_safe_preprocessed/execution.lock ? no-rerun marker.
- docs/LIVE_PROVIDER_SMOKE_TEST.md ? updated report, preserving the first-stage evidence.

The OpenAI **technical compatibility smoke is complete**: both specified images ultimately reached the real model, validated and returned accounted results through the provider pipeline. Accuracy remains unproven, including this possible safe-image false positive. A later formal benchmark should use independently reviewed labels and explicitly measure false positives and uncertainty; this smoke is not that benchmark and no benchmark has been run.
