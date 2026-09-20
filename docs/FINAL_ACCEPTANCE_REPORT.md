# Day 1 final acceptance report

Executed 2026-09-19. Scope frozen. Ready for a local, explicitly mocked competition demonstration; not production-ready. Vision-v1 remains default and Vision-v2 experimental. No V2.1, model inference, benchmark, new dependency, label change or risk-policy change was made.

## Executed checks

| Check | Final result | What it establishes |
|---|---|---|
| Backend: from backend, `.venv/Scripts/python.exe -m pytest tests -q` | **298 passed, 0 failed**, 57.03 s; 2 dependency deprecation warnings | API/service/provider/risk/retrieval/workflow regression coverage with external HTTP blocked and mocked SDKs |
| Production browser suite: `npm.cmd run test:e2e` with E2E_BASE_URL=http://127.0.0.1:3002 and E2E_API_URL=http://127.0.0.1:8002/api/v1 | **21 passed, 0 failed**, 35.8 s | Actual frontend/API workflows plus route-stubbed component scenarios; not 21 live-model tests |
| Critical uploaded-photo closure browser test, `--repeat-each=2` | **2 passed, 0 failed**, separate fresh records | Upload, mock findings, risk display, human confirmation, actions, simulated reinspection, human closure, reload persistence and audit timeline |
| Grounded workflow integration test, parameterized twice | **2 passed, 0 failed**; included in the 298 | Real services/database/retrieval with a synthetic indexed corpus and injected AI; citation grounding retained through human closure |
| Prepared uncertainty fixture browser inspection | Passed | DEMO AI provenance, insufficient/uncertain evidence, 55% confidence, human-review warning visible |
| Lint / TypeScript / locale consistency | All passed | `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test:i18n`; 711 keys per locale |
| Production build | Passed | `npm.cmd run build`; frontend started successfully from the generated bundle |
| Backend/database/routes | Passed | Isolated database initialized/seeded; health, project, inspection and incident operations work; SQLite integrity_check = ok |
| Final local availability | Passed | Frontend 3002 and backend health 8002 both HTTP 200; backend reports mock and ready |
| Non-paid OpenAI connectivity | Passed transport check | Network-enabled DNS resolution and verified TLS; unauthenticated HTTPS returned 401 as expected. Does not prove authenticated inference or model availability |
| Preservation snapshot | **122 files checked, 0 changed** | Snapshot covers existing datasets, fixtures, reports, backend AI implementation/prompts and backend/.env |
| Credential checks | No configured key values found | Checked frontend source/public and 34 built browser asset files; inspected diagnostic logs without printing credentials. This is a targeted check, not a security audit |

The 2 repeated browser checks and 2 focused integration checks are separate executions; the integration cases are also included in the backend suite. Counts above must not be summed as unique tests. Browser tests that mention provider provenance use stubs and made no DeepSeek calls.

## Full workflow and its limits

The browser uploaded a genuine existing rooftop fixture through the application, received clearly marked mock findings, displayed evidence and deterministic risk, showed sample demo regulation cards, required a human to confirm findings, created incidents, completed actions, ran simulated rectification reinspection, and waited for human closure. Refreshes retained the closed state and human audit event. The critical browser path was repeated with fresh records. No JavaScript page errors were recorded by that test.

Grounded regulatory retrieval was checked separately through actual backend API/workflow services with a temporary indexed synthetic source and injected provider. Two fresh database runs verified retrieval/citation grounding, no incident before confirmation, rejection of premature closure, required action completion, reinspection remaining in REINSPECTION, rejection of an AI closure actor, explicit human closure, persisted records and audit events. Citation grounding records survived closure. Other backend tests cover invented/missing citations and visible provider failures. This does not constitute live legal applicability validation.

The browser rejection scenario uploaded the existing ambiguous image, rejected the fixed mock proposals with a human reason, created no incident and retained rejection after refresh. An additional prepared synthetic response gives the same existing image 55% confidence and explicit uncertainty; its UI display was checked. Neither mock result is an actual interpretation of the image. The script must disclose sample regulation data and simulated mitigation, and must not represent these as live recognition or verified real-world rectification.

## Initial failures and fixes

1. **Blocking frontend HTTP 500:** Turbopack treated frontend as its filesystem root and could not resolve shared sibling locale JSON files. Set its root to the existing project parent in next.config.ts. Development routes then returned 200; production build and full production browser suite passed. No interface redesign.
2. **Browser test environment mismatch:** analyst tests hardcoded backend port 8000 while the isolated rehearsal uses 8002. Tests now accept E2E_API_URL with the existing 8000 default. No API contract changed.
3. **Transient browser assertion:** a language-change test observed two headings during hydration. It now waits for exactly one before checking visibility. Final production suite passed.
4. **Backend test environment contamination:** workload-specific settings loaded from the developer .env overrode legacy mock selection and reinspection dependency overrides. The test fixture now resets vision/reinspection provider, reinspection model and prompt version with reversible monkeypatches; individual provider tests still choose their own configuration. Production configuration and .env were not edited. External HTTP remains forbidden in tests.
5. A first backend run from the repository root had 296 passes and one relative-path .env.example test failure. The expected backend working directory resolved that failure. After extending integration coverage, a backend run had 286 passes/12 failures from environment contamination; an intermediate isolation run had 297 passes/1 reinspection failure. Final full run: 298/0. An earlier browser suite had 20 passes/1 hydration assertion failure; final full production run: 21/0. Initial 500/connection-refused diagnostic attempts were failures, not acceptance passes.

No incorrect incident-state, citation-grounding or human-confirmation bypass requiring a product-logic change was demonstrated. The frontend root configuration is the sole product runtime fix.

## Files changed or created

Modified:
- frontend/next.config.ts
- frontend/e2e/analyst.spec.ts
- frontend/e2e/i18n.spec.ts
- frontend/e2e/workflow.spec.ts
- backend/tests/conftest.py
- backend/tests/test_knowledge.py
- backend/.env.example (documents the existing V1 default; no secret values)

Created:
- scripts/start_day1_backend.ps1
- scripts/start_day1_frontend.ps1
- scripts/prepare_day1_uncertainty.py
- docs/FINAL_DEMO_SCRIPT.md
- docs/FINAL_ACCEPTANCE_REPORT.md
- docs/FINAL_COMPETITION_CLAIMS.md
- docs/DAY2_SUBMISSION_CHECKLIST.md
- docs/day1-preservation.json

Runtime artifacts: isolated backend/data/day1-demo.db and day1-uploads; frontend production build, Playwright report/screenshots (including test-results/day1-uncertainty.png). Next.js generated frontend/AGENTS.md and frontend/CLAUDE.md during development startup. These runtime/framework files are not new product features. Existing production DB, benchmark evidence, image labels and secrets remain separate. The repository already contains untracked project files, so this list describes this task's edits rather than treating all untracked files as newly created.

## Demo handoff

Use FINAL_DEMO_SCRIPT.md for exact PowerShell commands, photograph paths, click sequence, expected results and recovery. At completion, production frontend http://127.0.0.1:3002 and isolated mock backend http://127.0.0.1:8002 are running. Do not start another copy on those ports while they remain active.

Scenario A: existing rooftop photo -> explicitly mock findings -> risk -> sample regulations -> human confirmation -> actions -> simulated reinspection -> human closure/audit. Scenario B: existing ambiguous photo with an explicitly prepared uncertainty response -> human review -> rejection without unsupported incident creation. Prepared uncertainty inspection 26 is available in the isolated database; the helper can create a fresh entry if later records push it out of history.

## Remaining limitations and Day 2

- No authentication/authorization; role selection is a demonstration identity. Bind to loopback; do not present this as production security.
- The scripted demo intentionally does not prove live visual accuracy. No authenticated model request was made today. Non-paid transport checks do not guarantee future paid inference availability.
- Isolated demo regulation cards are samples. Actual grounding tests use a synthetic corpus; historical local RAG evaluation is a separate evidence source. Do not equate any citation with legal correctness.
- Historical V1 pilot and V1/V2 development metrics are small, non-independent datasets. V2 lost recall/F1 overall; it remains experimental. Claims and limitations are recorded in FINAL_COMPETITION_CLAIMS.md.
- Original photo reuse does not prove mitigation. Reinspection in the walkthrough must remain explicitly simulated.
- Backend test dependencies emit two deprecation warnings; they did not fail tests. No dependency migration was attempted during scope freeze.
- Photograph publication permissions/attribution and final package contents must be checked before recording/sharing. No submission, video or slide deck was created.

Day 2: rehearse; prepare a concise presentation from measured claims; record the labeled mock walkthrough; update README links to tested startup and dated reports; package permitted files while excluding credentials/private data; perform final security and submission-format checks. See DAY2_SUBMISSION_CHECKLIST.md.

**Paid model API calls: 0. OpenAI inference calls: 0. DeepSeek inference calls: 0. No benchmark executed.**
