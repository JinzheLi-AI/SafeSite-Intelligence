# Benchmark connectivity diagnosis

Date: 2026-09-17. Full benchmark was not restarted.

## Root cause and evidence

The restricted Codex shell reproduced a local Windows socket permission denial. Sanitized exception chain:

`httpx.ConnectError -> httpcore.ConnectError -> PermissionError(errno=13, winerror=10013)`

WinError 10013 means the socket operation was forbidden by access permissions. DNS resolved api.openai.com, but connection creation was denied before a TLS session or HTTP response. No certificate failure, timeout, refused/reset connection, or proxy error was observed in this reproduction.

The identical Python environment, provider client and official endpoint succeeded when launched through the approved network-enabled execution path: DNS resolved, TLS certificate verification remained enabled, and an unauthenticated GET /v1/models returned HTTP 401 as expected. This request sent no API key and invoked no model. Then one authorized production inference succeeded in that same execution context.

The present environment-specific restriction is confirmed by this controlled comparison. It is strongly supported as the cause of the earlier four benchmark failures. Those original records only retain connection_error, so their historical inner exceptions cannot be recovered verbatim. There is no evidence of an OpenAI outage, invalid key, model incompatibility or billing failure.

## Configuration and environment comparison

- Both benchmark and successful smoke runner change directory to backend before importing settings; both load backend/.env via the same Settings class.
- Both use RealMultimodalSafetyAIProvider. The smoke factory resolves to that implementation; the benchmark constructs it directly.
- Official fixed base URL: https://api.openai.com/v1/. Model: gpt-5.6-sol. Prompt: vision-v1.
- Provider timeout: 90 seconds. SDK max_retries=0; single-check validation_attempts=1.
- HTTP_PROXY, HTTPS_PROXY, ALL_PROXY and NO_PROXY were unset in the restricted diagnostic shell. No proxy credentials were displayed.
- TLS verification was not disabled. The provider uses its existing default verified HTTP transport.
- The two runners share preprocessing; all 20 files passed the prior benchmark preflight. The safe image also passed preprocessing in this check and its processed bytes were verified in the outgoing live request.
- The material observed difference is shell execution permissions, not provider/application code. The restricted Codex shell cannot be assumed to have the network access of an ordinary backend process. The approved execution path was tested; the already-running application process environment was not inspected or changed.

## Minimal resolution

Use the approved network-enabled execution context for authorized live work. No firewall, sandbox configuration, proxy, TLS, timeout, provider configuration, .env secret, model or production code was changed. Security controls remain in place; a reviewed execution permission was used rather than bypassing them. The default restricted shell remains unable to connect.

## Live check

Exactly ONE inference attempt, zero automatic retries:

- Image: evaluation/fixtures/live_smoke/01_safe.jpg; original preserved.
- Success: true; structured production output cached separately.
- Requested and returned model: gpt-5.6-sol.
- Prompt: vision-v1.
- Input tokens: 3813; output tokens: 501; total: 4314.
- Provider latency: 12328 ms.
- Estimated cost: unavailable; no pricing was invented.
- Cache: evaluation/reports/openai_connectivity_check/result.json.
- One-shot guard: evaluation/reports/openai_connectivity_check/execution.lock.

The diagnostic made two non-inference HTTPS attempts (restricted failed locally, approved returned HTTP 401), plus the one authorized inference. No DeepSeek call or benchmark execution occurred. During regression testing, one unintended reinspection provider connection was attempted by a test that loaded backend/.env; it was blocked by the restricted network and returned no inference response. This is an additional local inference attempt and is disclosed rather than counted as a successful or confirmed billable API call. A successful check demonstrates current connectivity, credential and model access, not guaranteed future service reliability or future billing capacity.

## Files created

- evaluation/check_openai_connectivity.py: non-inference unauthenticated connectivity check; sanitized exception types/codes only.
- evaluation/check_openai_live_once.py: explicit one-shot production check with permanent lock, one request and no retries.
- evaluation/reports/openai_connectivity_check/result.json and execution.lock: separate evidence.
- docs/BENCHMARK_CONNECTIVITY_DIAGNOSIS.md: this report.

Ground truth, all 20 image hashes and the production prompt hash still match the frozen benchmark record. RiskEngine, RAG, architecture, metrics and prior benchmark evidence were not changed.

## Verification and next command

Provider/preprocessing regression results are recorded below. The initial test invocation from the repository directory failed collection because app was not on Python's import path; running from backend then exposed live-.env contamination: 70 tests passed and two failed (provider selection and a blocked real reinspection connection). The final corrected test command runs from the repository root with PYTHONPATH pointing at backend, avoiding loading backend/.env. No test assertions or product files were changed. This was a test-launch issue, not an inference failure.

Run this non-paid check from an ordinary network-enabled PowerShell terminal:

```powershell
& '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite\backend\.venv\Scripts\python.exe' '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite\evaluation\check_openai_connectivity.py'
```

Expected: dns_resolved True, unauthenticated_https_status 401, tls_verified True. In Codex, the check requires approved network-enabled execution.

Connectivity is ready in the approved execution context. The benchmark is NOT automatically ready to relaunch: its existing execution.lock intentionally prevents overwriting or repeating the failed pass. Keep it and all old reports. The next benchmark task should explicitly authorize a fresh run with a separate output directory and unchanged frozen labels/prompt. No command to delete the lock or rerun the 20 cases was executed here.

Official reference: [OpenAI API error guidance](https://developers.openai.com/api/docs/guides/error-codes) distinguishes connection errors from API status failures and recommends checking network, proxy and SSL configuration. The root-cause conclusion above is based on local measurements, not an outage assumption.

Test command (from safesite): set the process-only PYTHONPATH to the absolute backend directory, then run `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_real_provider.py backend/tests/test_image_preprocessing.py -q`.
Final isolated regression result: **72 passed**, two existing dependency deprecation warnings. No production changes were required.
