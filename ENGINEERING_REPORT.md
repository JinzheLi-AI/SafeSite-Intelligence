# Engineering delivery report

## 1. Implemented

Complete Next.js + FastAPI monorepo and persistent mock vertical slice. Five navigation pages, incident detail, image evidence upload, nine core domain entities plus persisted knowledge documents, deterministic risk, human review, corrective actions, reinspection, explicit human closure, audit timeline and AI execution ledger.

## 2. Architecture decisions

Modular monolith. SQLAlchemy 2.x portable database types with SQLite foreign keys enabled; PostgreSQL migration requires a driver, migrations and data transfer. AI is isolated behind SafetyAIProvider. Business services own scoring, state transitions and persistence. Confirming an inspection creates one incident per hazard, avoiding unconfirmed AI-created cases. Original AI descriptions are preserved when humans modify accepted descriptions.

## 3. Structure

backend/app/{core,db,models,schemas,api,services,repositories,ai,seed}; backend/tests; frontend/src/{app,components,lib}; frontend/e2e; docs/screenshots.

## 4. Run frontend

From frontend: npm ci, copy .env.example to .env.local, then npm run dev. Production: npm run build, then npm run start. URL: http://127.0.0.1:3000. The local production frontend was started during delivery.

## 5. Run backend

From backend using the created Windows virtual environment:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs. A local API process was started during delivery. First-time installation and non-Windows setup are in README.md.

## 6. Seed/reset

Development startup seeds automatically, idempotently. Manual: python -m app.seed.demo. Stop the API and use python -m app.seed.demo --reset to drop configured application tables and recreate the seed. Uploaded files are retained. Seed includes 18 historical incidents, three sites, three unverified documents and one pending human-review Tower A inspection.

## 7. Verification

| Check | Result |
| --- | --- |
| pytest | 31 passed |
| Frontend ESLint, zero-warning policy | Passed |
| TypeScript strict typecheck | Passed |
| Next.js production build | Passed; all five pages plus incident detail |
| Real Chromium/Edge browser suite | 3 passed |
| Knowledge/analyst browser regression after database-backed documents | 1 passed |
| Health / documents / seeded inspection HTTP verification | Passed |
| Visual review | Dashboard, inspection form and incident/reinspection screenshots inspected |

Backend tests include threshold boundaries, policy override, low confidence, API validation, analysis persistence/idempotency, human confirmation/modification/rejection, invalid closure, full reinspection/closure, audit, structured output, provider failure rollback, server-side score enforcement, image validation, seed idempotency and concurrent confirmation.

Browser verification covers create/analyze/confirm, both corrective actions, explicit demo evidence, reinspection, human close, refresh persistence at multiple stages, no JavaScript page errors on the core workflow, all five laptop layouts, mobile navigation, no page-width overflow, document search/preview and honest analyst states.

Two upstream deprecation warnings remain in FastAPI/Starlette's test-client stack (httpx adapter and anyio BlockingPortal alias). Tests still pass. The browser runner emits an environment color-setting warning; the application has no associated runtime error.

## 8. Exact demo path

Dashboard → AI Inspection → Analyze Site → Human Review Required → Confirm Findings → Open primary incident → Start Rectification → complete both corrective actions → select simulated evidence or upload an image → Run Reinspection → review 85 → 15 and Eligible For Closure → Close Case → refresh and review the audit trail.

A prepared seed inspection is available at /inspections?id=19 in the delivered local database. A browser-verified closed example is /incidents/21. These IDs are examples from the current database, not hard-coded application assumptions.

## 9. Known limitations

AI analysis and reinspection are simulated and do not interpret image content. Regulations are authored sample data, explicitly Demo / Unverified. Analyst querying and real document ingestion/RAG are intentionally deferred. Demo actor names are not authenticated. Local evidence storage, synchronous provider calls, create_all initialization and bounded record lists suit this foundation; migrations, identity, rate limits, provider timeouts and deployment hardening remain future work.

Browser tests create database records. The current local database therefore contains additional test-created cases beyond the pristine seed. Reset instructions are documented.

## 10. Bugs/unfinished scope

No known blocking bug in the implemented, verified demo path. Two browser-discovered defects were fixed: asynchronous checkbox feedback and mobile overflow from an absolutely positioned accessibility label. Real AI, verified retrieval and analyst answers remain the explicitly planned next phase; excluded BIM/CCTV/IoT/etc. were not added.

## 11. Recommended next step

Integrate one real multimodal provider behind SafetyAIProvider, using a small evaluation set of construction images and the existing structured contracts. In parallel in the next development phase, curate a small verified regulation collection and implement provenance-preserving retrieval. Retain deterministic scoring and all human transition guards. Add identity/RBAC and reviewed database migrations before shared deployment.

## Important created files

See FILE_INVENTORY.md for the complete source/configuration inventory. Primary implementation entrypoints:

- backend/app/main.py
- backend/app/core/config.py
- backend/app/db/session.py
- backend/app/models/entities.py and documents.py
- backend/app/schemas/contracts.py
- backend/app/services/workflow.py, risk.py and guidance.py
- backend/app/ai/provider.py and mock.py
- backend/app/api/inspections.py, incidents.py, overview.py and uploads.py
- backend/app/repositories/queries.py
- backend/app/seed/demo.py
- backend/tests/conftest.py and test_workflow.py
- frontend/src/app/layout.tsx, globals.css and all five route pages
- frontend/src/components/incident-detail.tsx, inspection-form.tsx, inspection-results.tsx, reinspection-panel.tsx
- frontend/src/components/shell.tsx, ui.tsx, risk.tsx, audit-timeline.tsx, incident-table.tsx, charts.tsx, image-upload.tsx, analysis-progress.tsx
- frontend/src/lib/api.ts, types.ts and use-resource.ts
- frontend/e2e/workflow.spec.ts and playwright.config.ts
- frontend/scripts/capture-demo.mjs
- Both .env.example files, dependency manifests/locks, lint/typecheck/build configuration
- README.md, IMPLEMENTATION_PLAN.md, ENGINEERING_REPORT.md, FILE_INVENTORY.md, .gitignore

## Technical references

ESLint is run separately from production builds, following the [Next.js installation guidance](https://nextjs.org/docs/app/getting-started/installation). Database sessions use SQLAlchemy's transaction/session patterns; see the [SQLAlchemy session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html).
