# OpenAI / DeepSeek vision smoke comparison

**Latest credential revalidation (2026-09-17 08:30 Asia/Shanghai): one safe-image request returned HTTP 402, documented by DeepSeek as insufficient balance. This replaces the previous 401 as the current blocker. Authentication appears to have passed, inferred from the account-balance response; inference has still not completed.** The earlier two-image attempt below is historical. See the credential-revalidation section at the end for the latest evidence.

Run date: **2026-09-17 Asia/Shanghai**, 00:50:04-00:50:08 (2026-09-16 16:50 UTC).

**DeepSeek smoke failed authentication for both images: HTTP 401, invalid_credentials.** Two DeepSeek requests were attempted, exactly one per image, with zero retries. No DeepSeek prediction, confidence, risk or token usage was returned. No new OpenAI calls were made. This is a compatibility smoke and a comparison of available evidence, not a formal accuracy benchmark or a model ranking.

## Configuration and documented compatibility

DEEPSEEK_API_KEY was present in backend/.env. A boolean equality check confirmed that the effective credential used by the adapter matched the file. Its value was never printed or written to results. The file was not changed.

Actual persisted configuration still selects OpenAI / gpt-5.6-sol for vision and reinspection, with deterministic Analyst. There is no configured DeepSeek model in .env. Following the explicit request for DeepSeek Flash, the runner selected **deepseek-flash** in a process-local settings copy. It did not silently switch models or modify deployment configuration. This is the exact requested API model identifier, not a verified returned model: authentication failed before a model response was available.

The current [official model table](https://api-docs.deepseek.com/quick_start/pricing/) identifies deepseek-flash as DeepSeek-V4.1-Flash with image support, and specifies https://api.deepseek.com as the OpenAI-compatible base URL. DeepSeek V4 Pro lacks image support and was not selected. No legacy model alias was used.

The [official vision guide](https://api-docs.deepseek.com/guides/vision/) documents inline base64 image_url blocks in user messages. The existing adapter sends text and image_url content to **POST https://api.deepseek.com/chat/completions**. The [Chat Completions reference](https://api-docs.deepseek.com/api/create-chat-completion/) documents response_format={type:json_object} and thinking={type:disabled}. The adapter already uses these options, stream=false, and its existing JSON-schema instructions. Its Pydantic validation remains necessary because JSON mode alone does not enforce a schema. Documentation supports the intended request shape; the 401 responses do not establish live schema or inference compatibility.

## Inputs and request safeguards

Only the two authorized fixtures were used. Existing preprocessing was reused without changes:

| Image | Original dimensions | Submitted dimensions | Submitted bytes | Match to saved OpenAI input |
| --- | --- | --- | --- | --- |
| 01_safe.jpg | 5118 x 7677 | 1600 x 2400 | 954,120 | Exact SHA-256 match |
| 02_obvious_hazard.jpg | 5614 x 3733 | 5614 x 3733 | 2,417,773 | Exact SHA-256 match |

The safe processed hash is 309c0a5720690a8492cbef62058ea1f45405873df5b009b947310d1bb58d23f3. The hazard input hash is 51fe0ae6c2a7c41486af2785fd905db62607d4dcb8c90c47d6291d4d8ec59611. Both original fixture hashes and .env remained unchanged.

The outgoing HTTP hook verified the official DeepSeek endpoint, exact model, JSON/non-thinking format and actual decoded image bytes. Filenames were absent from model messages. These checks establish the submitted payload, not that an authenticated model processed it. SDK retries were disabled, validation attempts were limited to one, and a durable execution lock plus an HTTP request counter enforced the two-request bound. The requested prompt version is **vision-v1**. No fallback or incident/database workflow action occurred.

## Actual results and saved OpenAI comparison

OpenAI figures below come exclusively from the saved smoke artifacts; OpenAI was not called during this task.

| Image / provider | Result / hazard | Confidence: overall / hazard | Human review | Deterministic risk | Input / output / total tokens | Call latency | Estimated USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Safe / OpenAI Sol | Success; tentative missing_ppe, eyewear | 0.78 / 0.78 | Required | 8, LOW | 3,813 / 729 / 4,542 | 15,879 ms | null |
| Safe / DeepSeek Flash | HTTP 401; no prediction | null / null | Not evaluated | Not evaluated | null / null / null | 1,716 ms | null |
| Hazard / OpenAI Sol | Success; tentative missing_ppe, eyewear | 0.78 / 0.74 | Required | 18, LOW | 3,861 / 643 / 4,504 | 18,886 ms | null |
| Hazard / DeepSeek Flash | HTTP 401; no prediction | null / null | Not evaluated | Not evaluated | null / null / null | 578 ms | null |

The DeepSeek latencies measure rejected requests, **not inference speed**, and cannot be compared as model-performance measurements. Both errors were normalized to invalid_credentials with a sanitized message that the provider rejected the key. Raw provider error bodies and credential headers were not stored. The exact reason the key is invalid cannot be determined from these sanitized responses.

### Visual evidence and unsupported inferences

**Saved OpenAI safe image:** workers reviewing a clipboard/device were not wearing visible eyewear; glasses appeared to hang from one worker's clothing. The model explicitly acknowledged that the pictured activity did not establish an eye-protection requirement. The missing_ppe candidate is a possible false positive: observable eyewear absence alone does not establish a PPE violation. Human review remained required.

**Saved OpenAI hazard image:** workers had gloved hands at a rebar cage; eyewear was not visible, but helmet brims, head positions and shadows obscured their eyes. PPE absence was not confirmed. The response also noted projecting rebar without inventing a new unsupported hazard category. Its fixed six-category coverage does not include every possible construction hazard. The LOW score applies to the returned PPE candidate, not the overall safety of the scene.

**DeepSeek, both images:** no model output exists. It is impossible to determine whether it would repeat the PPE false positive, return zero hazards, make unsupported visual claims or generate fake citations. No prediction is not a zero-hazard prediction. Its structured schema, category constraints, runtime RiskEngine result and human-review behavior therefore remain **unverified by this live run**. The existing implementation was not weakened to obtain an answer.

The saved OpenAI results used the unchanged RiskEngine: 2 x 2 x 2 = 8 for the safe-image candidate and 3 x 3 x 2 = 18 for the hazard-image candidate. Its regulation-related output contained search queries, not authoritative citations. No RAG call was made in either smoke harness.

## Usage, cost and limitations

- DeepSeek: **2 attempted requests, 0 successful inferences, 0 retries**. Actual input/output/total tokens are unavailable and retained as null, not fabricated as zero.
- New OpenAI calls in this task: **0**. Saved OpenAI totals: 7,674 input + 1,372 output = 9,046 tokens from its two earlier successful calls.
- Estimated total DeepSeek cost: **unavailable (null)**. No usage metadata was returned and the pricing registry is empty. Null is not a claim of zero billing. Public rate verification alone cannot recover missing usage.
- No superior model can be identified. The DeepSeek failure is an authentication result, not evidence about its safety accuracy, latency or cost relative to OpenAI.

## Compatibility findings and next step

No product compatibility fix was necessary or attempted. Existing provider, preprocessing, prompts, RiskEngine, RAG, incident workflow and frontend files were unchanged. The only added code is a bounded one-shot DeepSeek smoke runner derived from the prior harness. It was syntax/preflight checked before sending, including matching both effective image hashes to saved OpenAI evidence. No regression suite was run because no product code changed, as requested.

**DeepSeek is not ready for formal benchmarking on this setup.** The prerequisite is a valid authorized DeepSeek API credential accepted by the official endpoint. Correct or replace DEEPSEEK_API_KEY privately in backend/.env, then explicitly authorize a separate bounded rerun. No further request is attempted or scheduled here; the current budget is exhausted. An authenticated smoke must pass before model-output comparisons are meaningful. Two images would still be insufficient to establish comparative accuracy.

Artifacts:

- [Actual DeepSeek results](../evaluation/reports/live_deepseek_smoke/results.json)
- [DeepSeek one-shot runner](../evaluation/live_deepseek_smoke.py)
- [Saved OpenAI safe-image result](../evaluation/reports/live_openai_safe_preprocessed/results.json)
- [Saved OpenAI hazard-image result](../evaluation/reports/live_openai_smoke/results.json)
- [Existing OpenAI smoke report](LIVE_PROVIDER_SMOKE_TEST.md)

Created in this task: evaluation/live_deepseek_smoke.py, evaluation/reports/live_deepseek_smoke/results.json, evaluation/reports/live_deepseek_smoke/execution.lock and docs/OPENAI_DEEPSEEK_SMOKE_COMPARISON.md. No API keys are included in these artifacts.


## Single-request credential revalidation ? 2026-09-17

Time: 08:30:29-08:30:32 Asia/Shanghai (00:30 UTC). Exactly **one additional DeepSeek request** was made using only 01_safe.jpg. SDK retries were zero and validation attempts were one. No OpenAI call, second-image call, model substitution or benchmark was performed.

The credential was present in backend/.env, and a private equality check confirmed that the adapter used that file's credential. No key value was exposed. Existing production vision configuration still selects OpenAI; this explicitly authorized test selected deepseek-flash in a process-local copy, preserving .env. The [official vision documentation](https://api-docs.deepseek.com/guides/vision/) still documents deepseek-flash image input at base URL https://api.deepseek.com, using POST /chat/completions with image_url data URLs. The model, endpoint and existing request format were not changed.

| Item | Observed result |
| --- | --- |
| HTTP status | **402** |
| Official error category | **Insufficient Balance** |
| Existing SafeSite normalized category | provider_unavailable |
| Authentication | Appears accepted, inferred from balance rejection instead of 401; no successful inference response |
| Requested model | deepseek-flash |
| Actual returned model | Unavailable; no model response |
| Prompt version | vision-v1, unchanged |
| Inference completed | No |
| Structured output validation | Not reached; no output |
| Hazards / confidence / human review / risk | Unavailable, not zero hazards |
| Input / output / total tokens | null / null / null; no usage metadata |
| Request latency | **2,023 ms** |
| Provider operation elapsed | 2,595 ms including local preprocessing |
| Estimated USD cost | null; unavailable, not asserted as zero |
| Additional requests | 1, no retries |

[DeepSeek's official error documentation](https://api-docs.deepseek.com/quick_start/error_codes/) distinguishes 401 authentication failure from 402 insufficient balance. Therefore the observed status suggests the credential is now accepted and the account balance is the blocking issue. The sanitized response alone does not prove inference/model-access/schema compatibility, and no raw error body or credential header was retained. The current adapter maps this non-special-cased HTTP status to provider_unavailable; the report preserves the exact 402 alongside that generic application category. No error-mapping or product-code change was made merely to relabel the result.

Existing preprocessing produced the same 1600 x 2400 image and 954,120 bytes as the saved OpenAI safe-image call. The outgoing HTTP hook verified those exact bytes and the official DeepSeek URL/model. The original image hash and .env hash remained unchanged. A before/after hash check confirms every existing backend/app source/config file remained unchanged. RiskEngine, RAG, prompts, image processing, provider request logic and incident workflow were untouched. Runtime RiskEngine integration could not be verified because authentication/account checks stopped the request before observations were returned. No incidents were created or closed.

**Readiness for the second image: not yet.** Resolve the DeepSeek account-balance issue privately, then separately authorize a successful bounded safe-image inference check before proceeding. No further call is made or scheduled. This task's one-request allowance is exhausted. Total DeepSeek attempts across these recorded tasks are three: two historical 401 responses and this single 402 response; none completed inference.

No product compatibility fix was required or justified by this result. The only additional executable artifact is a single-request evaluation harness derived from the existing one; existing implementation files were not edited. Its syntax and one-request constraint were checked, and no product regression suite was run because product code did not change.

Evidence: [credential-revalidation results](../evaluation/reports/deepseek_credential_revalidation/results.json), [one-shot test harness](../evaluation/live_deepseek_credential_check.py). A separate execution.lock preserves the no-rerun guard and earlier evidence remains intact.
