# Final competition demonstration - Day 1

Scope frozen: Vision-v1 is the production default. Vision-v2 is experimental and is not claimed to be more accurate overall. No V2.1, image collection, new benchmark or extra agent system. This is a local trusted competition prototype, not a production deployment.

## Startup - Windows PowerShell

Existing dependencies: backend .venv, frontend node_modules, Node/npm and Microsoft Edge for browser tests. Backend secrets stay in backend/.env; do NOT copy/overwrite that file. The demo scripts override provider selection only in their process and use a separate SQLite database and upload folder. No API key is required for the demo.

Terminal 1:

```powershell
Set-Location '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite'
& .\scripts\start_day1_backend.ps1
```

Terminal 2 (production build already prepared and tested):

```powershell
Set-Location '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite'
& .\scripts\start_day1_frontend.ps1
```

If rebuilding is needed, in frontend set `$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8002/api/v1'`, run `npm.cmd run build`, then the frontend launcher. API URL is embedded at build time. For local development only use `start_day1_frontend.ps1 -Development`; do not run dev and production against the same .next folder concurrently.

Browser: http://127.0.0.1:3002
Backend: http://127.0.0.1:8002/api/v1/health
API documentation: http://127.0.0.1:8002/docs

Settings applied by launcher: mock vision and reinspection, vision-v1, deterministic analyst, local fastembed, AUTO_SEED=true, DATABASE_URL=sqlite:///./data/day1-demo.db, UPLOAD_DIR=./data/day1-uploads, CORS limited to the demo frontend. Existing product DB, uploaded photographs, .env and benchmark evidence are preserved. V2 opt-in setting is documented in backend/.env.example; leave V1 selected for the submission.

## Before presenting (one minute)

Confirm health reports mock and ready. Say: "This walkthrough uses prepared mock observations and simulated rectification, so it is repeatable and incurs no model calls. The image upload, database, risk policy, human decisions and audit trail are real application operations." Do not call it live image recognition. Demo regulation cards are sample data, visibly labeled; the grounded retrieval integration is tested separately and historical corpus evidence is documented in FINAL_COMPETITION_CLAIMS.md.

## Scenario A - elevated work and an open edge (4-5 minutes)

Existing photograph:
`evaluation/fixtures/vision_v2/development/fbfd230b416044a7919c81f26bf501e8867a90ff9b24be50a4bf0f6cfa54ebdf.jpg`
This is the existing rooftop photograph with a person on a visibly elevated slab and open perimeter. Use its recorded source/attribution in any shared video. The mock output is a fixed scenario, not an assessment generated from this photograph; unseen fall-arrest equipment cannot be proven absent.

1. Open Dashboard, show persisted incident metrics. Choose EN for this script.
2. Click New AI inspection. Select the photograph with Browse files; enter a clear demo location.
3. Click Analyze Site. Show Analysis source: DEMO AI, visual evidence and human-review requirement. Two fixed hazard proposals appear: working_at_height and unprotected_edge.
4. Expand the risk explanation: first finding CRITICAL 85 (WAH policy), second HIGH 60. Explain that deterministic policy calculates risk, not an LLM score.
5. Show Demo regulation data. Explain its sample status; do not describe it as an official retrieved citation. Actual grounding and absent-evidence behavior are covered in the acceptance report.
6. Before confirming, show that no incident has been created for this inspection. Enter reviewer/assignee and notes, then Confirm Findings. Two incidents are created; open the primary incident.
7. Close Case is unavailable. Click Start Rectification and check each corrective action as completed.
8. Explicitly check Use simulated rectification evidence for this demo, then Run Reinspection. Never represent the original unrectified photo as real completion evidence.
9. Show Hazard Mitigated / closure eligibility; the case is still REINSPECTION. Refresh to demonstrate persistence.
10. Click Close Case as the human decision. Refresh; show CLOSED and Case Closed By Human in the audit timeline. The related incident remains separate and open until it receives its own complete workflow.

## Scenario B - uncertainty and refusal to overclaim (2-3 minutes)

Prepare a fresh labeled mock fixture while the isolated backend is running:

```powershell
Set-Location '[LOCAL_HOME]\Documents\ChatGPT\海之子\safesite'
& .\backend\.venv\Scripts\python.exe .\scripts\prepare_day1_uncertainty.py
```

This uploads existing `evaluation/fixtures/live_smoke/03_ambiguous.jpg` and creates a new mock-provider inspection using existing workflow services. It does not call a model. It is explicitly named DAY1 B ? OFFLINE uncertainty fixture and its model provenance is offline-uncertainty-fixture. The image and all benchmark labels remain untouched. This is a scripted response, not replayed live inference.

1. Open AI Inspection; select DAY1 B ? OFFLINE uncertainty fixture in Inspection history (latest eight items). Rerun preparation to create a fresh visible record if necessary.
2. Show DEMO AI, 55% confidence, Insufficient / uncertain evidence, and Human Review Required. Confidence does not discount the risk score.
3. Explain the view cannot establish the work/protection facts; neither zero hazards nor a rejected finding proves overall site safety.
4. Enter a reason: "Insufficient visible evidence; arrange qualified site review. Do not create an unsupported incident from this mock proposal."
5. Click Reject Findings. Show no incidents created, retained original proposal/reviewer explanation, and persistence on refresh. Do not close an incident because the image is ambiguous.

Optional 30-second evidence screen: show the saved live V1/V2 comparison report, clearly dated and cached; explain V2 reduced some false positives but lost recall/F1. Do not run the benchmark during the demo.

## Recovery

- Backend down: restart the backend launcher; check health. Do not delete the database. Seed is idempotent.
- Frontend down: restart the launcher; if the bundle targets another API URL, rebuild with the documented URL. Both modes were tested.
- Port occupied: inspect the existing process; reuse the intended server or stop it deliberately. Do not blindly kill unrelated applications.
- Analysis fails: show the error, retain the inspection, refresh/use its saved-analysis retry only in MOCK mode. No silent fallback. Live paid retries require separate authorization.
- Grounded index unavailable in the isolated demo DB: say so. Never substitute a sample citation and call it verified. Use the documented historical RAG evidence and offline integration-test evidence separately.
- Reset rehearsal: stop the backend and back up day1-demo.db before any manual reset. Do not reset the production database or benchmark records. Rehearsals normally need only fresh inspections.

Total presentation: about 7-9 minutes. Stay in mock mode. No paid API execution is part of this script.
