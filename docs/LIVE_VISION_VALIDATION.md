# Live vision validation and recovery report

Date: 2026-09-11. Local development engineering record; not a benchmark.

## Live validation status
Credentials were checked through the backend Settings object without printing, copying or logging the API key.
- Effective provider: mock
- OPENAI_API_KEY present: no
- Effective model: gpt-5.6-terra (configured default; availability not live-verified)
- Actual live/paid model calls made during this task: **0**

Live validation stopped at the credential check. No photographs were submitted, no new evaluation image set was selected, and no synthetic or offline output is presented as live evidence.

| Case | Intended scene | Live result | Reason |
| --- | --- | --- | --- |
| A | Obvious supported hazard | NOT TESTED | No API credentials |
| B | Relatively normal/safe scene | NOT TESTED | No API credentials |
| C | Ambiguous or occluded scene | NOT TESTED | No API credentials |
| D | Multiple supported hazards | NOT TESTED | No API credentials |

For each case, image filename, observations, returned hazard types, confidence, human-review flag, suggested factors, deterministic score, latency and reasonableness assessment are unavailable. False positives, false negatives, overconfidence, unsupported height/PPE inference and semantic duplication are **not assessed**. None can be reported as absent based on offline tests.

Real reinspection was not live-tested. Its existing offline controls passed regression tests. No repeatable live behavior was observed to justify prompt tuning: vision-v1 and reinspection-vision-v1 remain unchanged. RiskEngine and the six supported categories are unchanged.

## Stale-state recovery
No schema migration, new status, worker or external infrastructure was introduced.
1. Each analysis claim atomically changes CREATED to ANALYZING and appends AI_ANALYSIS_STARTED in the existing AuditLog, whose UTC created_at records its start. Its ID identifies the attempt.
2. Real-provider claims and their start event commit before inference, so a process interruption preserves the start timestamp.
3. POST /api/v1/inspections/{id}/analyze checks ANALYZING attempts. Their lease is max(300, 2 * SAFESITE_AI_TIMEOUT_SECONDS + 60) seconds: five minutes with the default 90-second timeout, seven minutes at the maximum 180-second timeout.
4. A fresh attempt returns HTTP 409 and remains protected. A stale attempt is conditionally returned to CREATED, with STALE_ANALYSIS_RECOVERED audit metadata. The same request starts a new attempt on the same inspection.
5. Legacy ANALYZING rows without a start event use inspection.created_at as a conservative fallback. This supports already-interrupted records without deleting or migrating them.
6. Success must conditionally reacquire ownership of the latest attempt before saving hazards. Late success from an expired attempt returns 409 and cannot overwrite the newer attempt. Late failure also cannot reset a newer attempt.
7. Ordinary real-provider failures restore CREATED and record AI_ANALYSIS_FAILED and failed AIExecution metadata. Existing uploads, descriptions, site associations and IDs are preserved.
8. Successful analyses remain idempotent: repeating analyze returns the saved result without another provider call.

Recovery is on demand when Retry is clicked; merely viewing history does not mutate records. ANALYZING inspections are now included in inspection history. Click the interrupted inspection, then Run saved inspection analysis after its stale window. No reupload is necessary.

## Tests
New backend tests in backend/tests/test_analysis_recovery.py:
- Stale timestamped attempt recovers, preserves metadata and succeeds.
- Legacy interrupted row recovers without a start event.
- Fresh analysis cannot be stolen.
- Ordinary provider failure records audit and remains retryable.
- Late success cannot overwrite a newer completed attempt.
- Late failure cannot reset a newer completed attempt.
- Start timestamp is persisted before real inference begins.

These are offline test doubles, not real model calls.
- Targeted backend run: 66 passed (7 recovery + 59 provider tests).
- Full backend suite, run once after targeted checks: **97 passed**.
- Existing dependency warnings: two FastAPI/Starlette test-client deprecations.
- Frontend lint/typecheck/production build: all passed.
- Browser tests: 7 passed (6 existing + 1 new interrupted-history/saved-image retry test).

## Remaining limitations and follow-up
- Live A/B/C/D recognition quality remains unvalidated because credentials are absent. Offline tests prove handling and boundaries, not visual accuracy or calibration.
- Recovery is request-driven, not a scheduled cleanup. An interrupted row remains labeled ANALYZING until retried.
- A request genuinely taking longer than its lease can be superseded. Its response is fenced out; an already-sent provider request cannot be canceled by this local recovery mechanism and may still incur a charge.
- Legacy rows lack a precise original analysis start, so creation time is the fallback.
- Local SQLite/synchronous execution and existing demo identity limitations remain.
- No live-derived bug fixes, new AI features, RAG, prompt tuning, risk changes or UI redesign were made.

## Reproducible future live record
After configuring credentials, select four distinct new local construction photographs. For each, record: case ID, filename (and optionally SHA-256), broad scene, actual model/prompt/provenance, returned hazard types, per-hazard/overall confidence, review flag, visual evidence, bounded severity/exposure/probability, final deterministic risk and overrides, execution latency, reasonableness judgment, false positives/negatives, unsupported inferences and discovered issues. Review the image itself when making those judgments. Four images are engineering checks, not formal accuracy measurement.

## Exact files changed for this task
- backend/app/services/workflow.py
- backend/tests/test_analysis_recovery.py
- frontend/src/app/inspections/page.tsx
- frontend/e2e/real-analysis.spec.ts
- docs/LIVE_VISION_VALIDATION.md
- README.md
- REAL_AI_IMPLEMENTATION.md
