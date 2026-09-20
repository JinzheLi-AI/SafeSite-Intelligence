# Multi-provider validation

Validation date: 2026-09-15. This change prepares controlled comparison; it makes no model-accuracy or superiority claim.

## Architecture and supported workloads

The existing safety provider protocol and OpenAI Responses adapter remain. A central factory resolves independent vision and reinspection settings. DeepSeek uses the existing OpenAI SDK against its documented Chat Completions endpoint, with JSON mode and local validation into the same Pydantic observations. Both safety adapters share normalization, six hazard categories, conservative review checks and deterministic RiskEngine. Analyst adapters propose the existing AnalyticsPlan; the existing SQL validator and semantic metric verification remain authoritative.

| Provider / reviewed model | Inspection | Reinspection | Analyst planning | Transport |
| --- | --- | --- | --- | --- |
| OpenAI / gpt-5.6-terra | Yes | Yes | Yes | Responses, strict structured output |
| OpenAI / gpt-5.6-sol | Yes | Yes | Yes | Responses, strict structured output |
| DeepSeek / deepseek-flash | Yes | Yes | Yes | Chat Completions, JSON mode, local schema validation |
| DeepSeek / deepseek-v4-pro | No | No | Yes | Chat Completions, JSON mode, local schema validation |
| mock / safesite-scenario-v1 | Simulated | Simulated | N/A | Offline |
| deterministic | N/A | N/A | Registered metrics | Offline |

The capability registry records text, images, structured JSON, strict schema, tools, usage and official source. Strict-schema=false for the chosen DeepSeek JSON-mode interface: JSON syntax alone does not establish schema compliance. This does not claim that every other DeepSeek API interface lacks strict tools. Unknown provider/model pairs fail closed until their capabilities are reviewed. Text-only DeepSeek Pro is rejected for image workloads before a request. No fallback or provider routing exists. Common Analyst questions remain deterministic even when flexible planning is enabled.

Official sources reviewed for this implementation:

- [OpenAI Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) and [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol): model capabilities and Responses support.
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs): structured response validation.
- [DeepSeek model capabilities and pricing](https://api-docs.deepseek.com/quick_start/pricing/): current canonical models, Flash image support, Pro text-only, cache and time-dependent prices.
- [DeepSeek vision](https://api-docs.deepseek.com/guides/vision/): image_url content and inline image bytes.
- [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/): JSON mode, non-thinking request option, finish reasons and usage fields.

## Configuration and secrets

Put actual keys only in ignored `backend/.env`, never in source, frontend environment variables, commands, screenshots or reports. `backend/.env.example` contains exactly empty OPENAI_API_KEY and DEEPSEEK_API_KEY assignments. Git check-ignore confirms `safesite/backend/.env` is ignored. Credential availability was checked as booleans only; neither key is available.

Example mixed configuration (fill keys privately in backend/.env):

```dotenv
SAFESITE_VISION_PROVIDER=openai
SAFESITE_VISION_MODEL=gpt-5.6-terra
SAFESITE_REINSPECTION_PROVIDER=openai
SAFESITE_REINSPECTION_MODEL=gpt-5.6-sol
SAFESITE_ANALYST_PROVIDER=deepseek
SAFESITE_ANALYST_MODEL=deepseek-v4-pro
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
```

For DeepSeek inspection/reinspection, set that workload's provider to `deepseek` and model to `deepseek-flash`. Each real workload requires only its provider's credential. A mixed OpenAI/DeepSeek deployment needs both because both are selected; OpenAI-only does not require DeepSeek's key and vice versa. `SAFESITE_VISION_PROVIDER=mock` and `SAFESITE_ANALYST_PROVIDER=deterministic` work without credentials.

Omitted reinspection provider/model independently inherit vision provider/model. If selecting a different reinspection provider, explicitly set its compatible model. Legacy SAFESITE_AI_PROVIDER=mock/real (and AI_PROVIDER alias) still maps to mock/OpenAI when SAFESITE_VISION_PROVIDER is absent. Explicit workload settings take precedence. Existing SAFESITE_AI_TIMEOUT_SECONDS, SAFESITE_AI_MAX_OUTPUT_TOKENS and SAFESITE_ANALYST_TIMEOUT_SECONDS still apply. SAFESITE_PRICING_FILE optionally points to a reviewed pricing JSON file. Restart the backend after edits.

Health reports vision and reinspection readiness separately. Analyst capabilities report its own readiness. These responses contain model identifiers and capability metadata, never credentials. Settings use SecretStr. Adapter errors store normalized codes and sanitized messages, never raw provider error bodies. Analyst logging redacts both configured keys. SDK retries are disabled; invalid safety output has at most two validation attempts, with no provider substitution.

## Usage and migration

The existing AIExecution remains one row per workflow execution. Five nullable columns are added: input_tokens, output_tokens, total_tokens, estimated_cost_usd and call_records. Startup performs an idempotent additive SQLite migration; existing rows retain null usage. No incident state migration or new observability page is introduced.

`call_records` contains one entry per attempted SDK call, including validation retries: workflow_name, provider, model_name, prompt_version, started_at, latency_ms, status, confidence where appropriate, token fields, estimated_cost_usd and error_message. Actual response ID/model and reported cache metadata are also retained. Successful workflow confidence is attached to successful attempts. Analyst confidence remains null because its contract has no confidence score. Parent totals sum attempts only when every attempt reports that field; otherwise the aggregate is null. Parent latency includes workflow work; per-attempt latency measures request and response validation. Deterministic/mock paths have no external-call records or invented usage.

OpenAI input_tokens/output_tokens/total_tokens and DeepSeek prompt_tokens/completion_tokens/total_tokens are normalized from actual SDK metadata. Cached input fields are preserved when reported. Image usage is whatever the provider reports, not an estimate from pixels or string length. Failed requests or SDK parsing exceptions that do not expose response usage leave it null. A failed request may still have incurred provider charges; null does not mean free. No prompts, image bytes, keys or raw errors are placed in call_records.

## Estimated cost

`backend/app/core/provider_pricing.json` is intentionally an empty registry. Token accounting works without prices. Current official DeepSeek rates vary with cache and peak/off-peak schedules; OpenAI pricing includes context/cache modes. A single unconditional rate would overstate reliability, so no default dollar estimate is asserted.

To configure an independently reviewed standard-token rate, add an exact provider/model JSON entry with:

- provider, model, effective_date and valid_until (inclusive UTC dates).
- source_note and source_url identifying official documentation, account assumptions and verification date.
- billing_mode=`standard_token`; input_price_per_million and output_price_per_million.
- cached_input_price_per_million when cached input has a different rate; otherwise uniform_input_rate=true only if all input is reliably billed alike.
- image_tokens_in_usage=true only when reported token totals fully cover image charges.
- max_input_tokens when the verified rate stops at a context threshold.

The estimate is `((input - cached) * input_rate + cached * cached_rate + output * output_rate) / 1,000,000`. A full copy of the pricing entry is retained with the call for audit. Dates, nonnegative finite rates and exact model matching are required. Missing usage/pricing, multiple applicable entries, expired entries, unknown cache counts with different cache rates, positive cache-write tokens, unsupported billing mode, context beyond the configured threshold, or unknown image billing all produce null. This small registry does not implement dynamic time-tier pricing, batch rates, cache-write billing or account discounts; leave those configurations unset. Tests use conspicuously synthetic rates, not suggested production prices. Actual token counts and estimated monetary cost are distinct; the estimate is never billing truth.

## Evaluation and next steps

Existing reviewed-case validation, image hashes and paired generic/SafeSite baselines are preserved. `--vision-model-id openai/<model>` or `deepseek/<model>` selects a reviewed image-capable model. Every result has provider/model/model_id; `vision-calls.json` records case_id, image hash, prediction, latency_ms, prompt_version, actual nullable tokens, estimated_cost_usd and per-attempt call_records. Separate output directories prevent one model run overwriting another. Use the same reviewed manifest/image hashes, case ordering, limit and validation-attempt setting for every model. Inspect errors and null usage alongside metrics; do not treat failed calls as free or claim accuracy from fixture tests.

1. Privately configure the required keys and model settings in backend/.env. Do not copy its contents into chat.
2. Supply licensed/consented real images and complete independent human review under the existing evaluation methodology. Current placeholder image manifests are not valid accuracy data.
3. From the `safesite` directory, the following is a small *future* paired comparison command, bounded to two external calls per provider (one case, two baselines, one attempt each):

```powershell
backend/.venv/Scripts/python.exe evaluation/run.py --live-vision --vision-model-id openai/gpt-5.6-terra --max-vision-cases 1 --vision-validation-attempts 1 --output evaluation/reports/openai-terra-small
backend/.venv/Scripts/python.exe evaluation/run.py --live-vision --vision-model-id deepseek/deepseek-flash --max-vision-cases 1 --vision-validation-attempts 1 --output evaluation/reports/deepseek-flash-small
```

Pass `--datasets <reviewed-dataset-directory>` and `--image-root <reviewed-image-root>` when stored elsewhere. Without reviewed images, output remains pending and no calls occur. A later OpenAI Sol comparison uses `--vision-model-id openai/gpt-5.6-sol` and a separate output directory. Increasing cases or attempts increases the billable bound: cases x 2 baselines x attempts. This command compares one case; it is not the separate two-image compatibility smoke described below and is not a meaningful accuracy benchmark.

## Validation and limitations

No live calls were made: OpenAI 0, DeepSeek 0. Neither credential was available. The requested obvious-hazard plus safe/ambiguous live smoke remains unperformed, not simulated as a success. Offline official-SDK MockTransport tests validate request construction; they cannot establish account access, actual current provider behavior or vision accuracy.

Product regression includes provider selection, independent readiness, missing keys, unsupported image models, same normalized safety output, zero/multiple hazards, invariant deterministic risk, malformed output and bounded retries, no fallback on authentication/rate/service/timeout errors, nullable and reported usage, migration preservation, dated cost arithmetic, human-only closure after DeepSeek reinspection, and unchanged Analyst SQL rejection. Evaluation tests cover provider/model output and unsupported image capability. Browser coverage includes DeepSeek provenance in the existing source display. Existing risk, RAG, SQL safety and prompt files are hash-checked against the task baseline.

Verified results: **267 backend product tests**, **34 evaluation tests**, and **20 browser tests** pass. Frontend lint, TypeScript, locale parity (711 keys per locale), and production build pass. The only Python warnings are existing Starlette/httpx and AnyIO deprecations. Tests prohibit external HTTP or use injected SDK responses/MockTransport; no test incurs API charges. No image benchmark was run and existing evaluation accuracy reports were not replaced. Twenty-one protected source hashes match the task baseline.

The local backend was restarted successfully, applying the nullable SQLite usage columns without a destructive migration. The frontend is serving the verified production build at http://127.0.0.1:3000.

## Exact changed source files

Paths below are relative to the safesite repository. Compared by SHA-256 against the pre-task inventory; the working tree contains earlier project work, so this list describes this task rather than every untracked repository file. Runtime database rows, Playwright reports/screenshots and ignored validation bookkeeping are excluded.


- `README.md`
- `backend/.env.example`
- `backend/app/ai/accounting.py`
- `backend/app/ai/capabilities.py`
- `backend/app/ai/deepseek.py`
- `backend/app/ai/provider.py`
- `backend/app/ai/real.py`
- `backend/app/analyst/adapters.py`
- `backend/app/analyst/provider.py`
- `backend/app/analyst/service.py`
- `backend/app/api/analyst.py`
- `backend/app/api/incidents.py`
- `backend/app/api/overview.py`
- `backend/app/core/config.py`
- `backend/app/core/provider_pricing.json`
- `backend/app/main.py`
- `backend/app/models/entities.py`
- `backend/app/services/workflow.py`
- `backend/tests/test_multi_provider.py`
- `docs/MULTI_PROVIDER_VALIDATION.md`
- `evaluation/run.py`
- `evaluation/runners/vision.py`
- `evaluation/tests/test_evaluation.py`
- `frontend/e2e/real-analysis.spec.ts`
- `frontend/src/app/analyst/page.tsx`
- `frontend/src/components/analysis-source.tsx`
- `frontend/src/components/reinspection-panel.tsx`
- `frontend/src/lib/types.ts`
