# Paired development runner

Added evaluation/paired_vision.py and evaluation/tests/test_paired_vision.py. No production provider, prompts, manifest, scoring semantics or historical reports changed. The approved development manifest fingerprint was verified unchanged.

## Commands (PowerShell, repository root)

```powershell
Set-Location '[LOCAL_HOME]\Documents\ChatGPT\???\safesite'
# Default offline: production provider with injected synthetic SDK responses, no external calls.
& .\backend\.venv\Scripts\python.exe -m evaluation.paired_vision
# Future LIVE ONLY in the approved network-enabled environment:
& .\backend\.venv\Scripts\python.exe -m evaluation.paired_vision --execute-live --network-enabled
```

Each command creates a unique directory. Explicit --output PATH must be new. To resume, supply the SAME path with --resume and the SAME mode flags. To reproduce live reports without calling providers, use --execute-live --report-only --output PATH; report-only never invokes inference. Offline report reproduction needs --report-only --output PATH only. No secret values are printed.

--network-enabled is an explicit operator acknowledgement, not an OS permission override. Start the live command only from the approved network-enabled execution environment. TLS verification remains enabled; the production provider fixes the official OpenAI endpoint. Network health and model access have NOT been retested live in this task.

## Pipeline and request limits

Ten ready development cases, alternating vision-v1 then vision-v2 per image, maximum 20 reserved attempts total. The runner calls RealMultimodalSafetyAIProvider.analyze_inspection and the normal image_data_url preprocessing. It explicitly sets vision_prompt_version on a per-invocation settings copy and verifies the actual outgoing system prompt and processed image bytes. The model gpt-5.6-sol, provider openai, high image detail, English output, timeout and output budget are shared. Actual output normalization and RiskEngine behavior come from the product. V1 lacks a comparable explicit uncertainty field; no aggregate mapping is invented.

SDK retries=0 and validation_attempts=1. A durable attempt reservation precedes every invocation. Responses are saved immediately when returned, before product normalization, then full normalized output, raw structured output, usage, returned model, timing and errors are saved. No incidents/workflows are invoked. Failure messages are sanitized categories, not raw exceptions/headers. Unknown usage remains null. Offline usage is null, and offline results are explicitly synthetic.

Two consecutive connection_error/timeout failures stop and persist stopped=true. A local execution error also stops. Failed or interrupted reservations are never automatically retried, including after resume; an interrupted request may have been billed and is conservatively unavailable. The runner does not automatically reset a stopped run. Preserve it for diagnosis rather than starting another run blindly. Concurrent writes use an exclusive run lock; never delete a live writer's lock.

## Cache identity

state.json is authoritative. Resume requires exact manifest bytes/snapshot, case IDs/hashes, processed hashes, provider/model, prompt hashes, timeout/output settings, provider/preprocessing/normalization/RiskEngine/scorer/runner implementation hashes and mode. Each record is keyed by prompt version + case ID and independently checked. Live cannot resume offline caches. Historical smoke caches are never imported. Editing code/settings or ground truth invalidates resume rather than silently mixing runs. Keep the original environment available for reproduction.

## Reports

Each run includes state.json, vision-v1_cache.json, vision-v2_cache.json, per-version metrics, paired_report.json and summary.md. Caches preserve the complete V2 snapshot and use vision-three-state-v1. Metrics/differences use the SAME intersection of successful cases for both versions. Unpaired success/failure/unattempted records remain visible in full per-case caches; common-case coverage is disclosed. No partial sample is presented as full coverage.

Reports include masked FP/FN case analysis, micro metrics, macro F1 difference, PPE FP count difference, safe-scene FP rate, recall and exact match, explicit uncertainty comparison only when fully comparable, tokens and average latency for each version. Undefined/incomparable differences are null. Original predictions are not modified. Missing usage is never fabricated.

Case 008 housekeeping is excluded from classification, its five other classes scored, and it is excluded from safe-scene and full-exact-match denominators. On full completion: 59 known image-class pairs, 9 exact-match cases, 3 safe scenes. Operational confirmation never counts as unnecessary uncertainty review.

## Offline verification

Verified output: evaluation/reports/paired_offline_step15_verified/. Synthetic empty-hazard SDK fixtures are deliberately independent of labels. They exercise actual prompt selection, preprocessing, product normalization and scorer/report/cache code, but their scores are NOT model performance. No real cached predictions were invented.

184 relevant evaluation/backend tests passed (two existing dependency warnings). Three paired tests passed again after the final runner fingerprint addition. Network-disabled tests verify all 20 schedules, differing actual prompts, matching processed bytes, scorer version, case 008, byte-identical report reproduction, no duplicate calls on resume, cache tampering rejection, interrupted reservation preservation, and stop-after-two behavior. Historical frozen-file regression checks pass.

Ready for an explicitly authorized live paired run in the approved network-enabled environment; actual network/API success remains unverified in this task. Maximum planned paid calls: 20. Zero paid/model API calls were made. No DeepSeek call or live benchmark was started. Ten development images are not independent held-out validation and do not justify statistical significance claims.
