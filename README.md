# SafeSite Intelligence

**A human-controlled construction safety inspection and incident-management prototype.**

SafeSite connects image observations, deterministic risk assessment, regulatory passage retrieval, human decisions, corrective actions and reinspection in one auditable workflow. This existing project includes a Next.js interface, FastAPI backend, SQLite persistence, bilingual content, offline tests and versioned evaluation tooling.

> Competition/research prototype, not a production safety authority. No authentication or authorization is implemented. Keep it local/trusted. A person confirms incidents and explicitly closes them. Mock outputs do not interpret photographs. Guidance is not a legal determination.

## Capabilities and architecture

- Dashboard, AI Inspection, Incidents, Safety Analyst and Knowledge Base; English and Simplified Chinese.
- JPEG/PNG/WebP upload with validation, orientation handling and oversized-image preprocessing.
- Independent mock/OpenAI/DeepSeek adapters, structured observations, usage metadata and explicit failures.
- Six categories: missing PPE, working at height, unprotected edge, unsafe scaffolding, electrical hazard and housekeeping.
- Deterministic risk factors/policy overrides, regulatory passage grounding, corrective actions, human decisions and audit history.
- Bounded read-only database analytics; optional model planning is separate from vision.
- Local annotation UI, dataset validation, indeterminate-aware scoring and resumable paired evaluation.

```text
Next.js / TypeScript / shared locales
                  | REST /api/v1
FastAPI + Pydantic contracts
                  +-- provider adapters -> structured observations
                  +-- deterministic RiskEngine
                  +-- registered retrieval / citation grounding
                  +-- human workflow guards / audit / analytics
                  |
           SQLAlchemy / SQLite + local evidence files
```

No incident exists until human confirmation. Reinspection eligibility is followed by a separate human closure command. Low confidence never lowers risk. Missing regulatory evidence remains missing; demo citations are separate. **Vision-v1 remains default; Vision-v2 is experimental and is not claimed to be superior overall.**

## Project layout

| Path | Contents |
|---|---|
| `backend/app/` | API, providers/prompts, contracts, risk/workflow services, knowledge ingestion, analytics and seed |
| `backend/tests/` | Offline unit/API/provider/security/workflow regression tests |
| `frontend/` | Existing Next.js application, browser tests, configuration and dependency lockfile |
| `shared/locales/` | English and Chinese translations |
| `evaluation/` | Annotation tools, validators, scoring, runners, manifests and historical results |
| `scripts/` | Demo launchers, uncertainty fixture helper and offline publication audit |
| `docs/` | Design, validation, labeling, error audits, demo and publication guidance |

Credentials, databases, uploads, downloaded PDFs/model weights, caches and installed dependencies are excluded. The publication proposal also includes ten credited Wikimedia development photographs and withholds twenty pilot photographs plus contact sheets/screenshots pending rights/privacy review. **The complete source implementation is retained, but this is not a self-contained benchmark image bundle.** Originals remain local. See [publication review](docs/PUBLICATION_REVIEW.md) and [third-party materials](docs/THIRD_PARTY_MATERIALS.md).

## Installation and startup

Requirements: Git, Python 3.12 (with the Windows `py` launcher), Node.js and npm. Verified local toolchain: Python 3.12.13 and Node.js 24.18.0. Dependency installation requires internet access unless all locked packages are already cached. If `py` is unavailable, install the Python launcher or use the full path to your Python 3.12 executable in the virtual-environment command. Do not overwrite existing environment files.

Clone the source, then open two PowerShell terminals in the new checkout root:

```powershell
git clone https://github.com/JinzheLi-AI/SafeSite-Intelligence.git
Set-Location SafeSite-Intelligence
```

**Fresh-install verification limit:** A fresh backend dependency installation has not been fully verified. The published source passed 31 backend workflow tests using an existing Python 3.12 environment; an offline fresh-install attempt could not resolve packages because its wheel cache was empty. Frontend dependencies installed from the local npm cache, and two mock browser tests passed. These checks do not establish a fully fresh online installation.

### Windows PowerShell: backend

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The example selects mock vision and deterministic analytics; no model key is needed. Startup initializes SQLite and idempotent demo seed data. Relative backend paths are `data/safesite.db` and `uploads/`.

Use a fresh terminal without inherited live-provider settings: environment variables override `.env`. Before the walkthrough, check the health URL below and confirm **both vision and reinspection report `provider: mock` and `ready: true`**. Leave API keys blank. Stop if a live provider is reported.

### Windows PowerShell: frontend, second terminal

```powershell
Set-Location frontend
npm.cmd ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm.cmd run dev
```

- Website: [http://127.0.0.1:3000](http://127.0.0.1:3000)
- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

For a production frontend served locally, stop dev, run `npm.cmd run build`, then `npm.cmd run start`. `NEXT_PUBLIC_API_URL` is public and embedded at build time; rebuild after changing it. Never put credentials in a `NEXT_PUBLIC_*` variable.

On macOS/Linux, use `python3.12 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.lock.txt`, and `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` from backend. Copy the example only when no `.env` exists. Use `npm ci` and `npm run dev` in frontend. These are equivalent instructions; final acceptance used Windows, not a fresh macOS/Linux installation.

### Isolated competition rehearsal

After dependencies are installed, run `scripts/start_day1_backend.ps1` from the project root. In another terminal, build the frontend with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8002/api/v1`, then run `scripts/start_day1_frontend.ps1`. The launchers use ports 8002/3002, mock providers and a separate Day 1 database/upload directory. Use `-Development` on the frontend launcher instead when a production build is not prepared.

Exact alternative commands, each starting at the checkout root:

```powershell
# Terminal 1
.\scripts\start_day1_backend.ps1
```

```powershell
# Terminal 2: development mode needs no prebuilt bundle
.\scripts\start_day1_frontend.ps1 -Development
```

Open http://127.0.0.1:3002/ for this alternative; check http://127.0.0.1:8002/api/v1/health. Do not run dev and production processes against the same frontend build directory simultaneously.

The [demo script](docs/FINAL_DEMO_SCRIPT.md) describes the existing local-fixture walkthrough. Substitute your checkout root for historical computer-specific paths. Photo-based helpers/browser tests require the documented permitted fixtures restored locally. The normal application accepts your own permitted photographs; mock mode still returns fixed demo findings rather than interpreting them.

### Complete mock workflow using a bundled, approved image

This walkthrough needs no API keys, regulatory index or excluded pilot photographs. Use EN in the interface so the button names match below. It works with either startup option above.

1. Open Dashboard, then **New AI inspection**.
2. Upload `evaluation/fixtures/vision_v2/development/fbfd230b416044a7919c81f26bf501e8867a90ff9b24be50a4bf0f6cfa54ebdf.jpg` from this checkout.
3. Click **Analyze Site**. Confirm **DEMO AI**, **Human Review Required**, and **Demo regulation data**. Findings are fixed mock observations, not analysis of the photograph; risk is calculated by the deterministic policy.
4. Click **Confirm Findings**, then **Open primary incident**. This human decision creates incidents; analysis alone does not.
5. Click **Start Rectification** and complete every corrective-action checkbox.
6. Select **Use simulated rectification evidence for this demo**, then **Run Reinspection**. This explicitly simulates evidence; do not describe it as a real repaired-site inspection.
7. Confirm **Hazard Mitigated**. The incident remains open until a human clicks **Close Case**.
8. Click **Close Case**, refresh, and inspect the closed status and **Case Closed By Human** audit entry. Other incidents created by the same inspection have their own workflows.

The bundled photograph is by Marek Ślusarczyk (Tupungato), CC BY 3.0: [source](https://commons.wikimedia.org/?curid=134276899), [license](https://creativecommons.org/licenses/by/3.0/). Preserve attribution in recordings. File-specific credits are in [PUBLICATION_MEDIA.json](docs/PUBLICATION_MEDIA.json).

The older demo script's **Scenario B** and tests using `evaluation/fixtures/live_smoke/` are not reproducible from this release alone: those photographs were intentionally withheld. Do not run the uncertainty helper expecting that image to be bundled. No screenshots are included because their redistribution/privacy review remains unresolved; do not add the excluded screenshots to remedy this.

## Configuration and real inference

See `backend/app/core/config.py`, `backend/.env.example` and `frontend/.env.example`.

| Setting | Purpose |
|---|---|
| `SAFESITE_VISION_PROVIDER` | `mock`, `openai`, `deepseek`; explicit setting overrides legacy selection |
| `SAFESITE_VISION_MODEL` | Requested model, subject to compatibility/account availability |
| `SAFESITE_VISION_PROMPT_VERSION` | `vision-v1` default; experimental `vision-v2` |
| `SAFESITE_REINSPECTION_PROVIDER`, `SAFESITE_REINSPECTION_MODEL` | Optional independent reinspection selection |
| `SAFESITE_ANALYST_PROVIDER` | `deterministic` default, optional model planning |
| `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` | Backend-only credentials; unnecessary for mock mode |
| `DATABASE_URL`, `UPLOAD_DIR`, `CORS_ORIGINS` | Persistence, evidence and permitted frontend origins |
| `SAFESITE_EMBEDDING_PROVIDER` | Local `fastembed` default or explicitly configured remote embeddings |

Live mode sends image bytes to the selected provider and can incur charges. Historical runs record `gpt-5.6-sol`; this is saved-run provenance, not a promise of current model availability. Verify provider capabilities, access and pricing before enabling it. Real failures never silently become mock predictions. Unknown pricing produces no cost estimate.

No live inference is part of installation/publication preparation. Read budgets and approval controls before running any `live_*`, live-check or benchmark script. Optional model-backed analyst planning is independent of vision.

## Regulatory retrieval

`backend/app/knowledge/hk_core.json` contains registered official source URLs. PDFs, model caches and vectors are local artifacts, not bundled material. Mock mode uses labeled sample citations and needs no populated index.

After reviewing source/use terms, the existing ingestion command from backend is:

```powershell
.\.venv\Scripts\python.exe -m app.knowledge.ingest --source-set hk_core
```

This downloads official documents and, with default fastembed, a local embedding model. Network/disk access is required. Remote embedding configuration may incur charges. `--offline` requires existing PDFs, receipts and model cache. Check results: source content can change. Grounding is correspondence to stored text, not legal applicability. Hong Kong is the currently indexed pilot jurisdiction.

## Tests and acceptance evidence

Backend, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Frontend, from `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test:i18n
npm.cmd run build
```

Browser tests require running mock services, Microsoft Edge (configured default) and permitted local fixtures. Set `E2E_BASE_URL` / `E2E_API_URL` for non-default ports, then run `npm.cmd run test:e2e`. Never run workflow tests against a live-provider backend. Offline evaluation tests are in `evaluation/tests/`; some require locally retained images/datasets. Tests are distinct from paid evaluation runners.

The 2026-09-19 local acceptance recorded **298 backend passes, 21 production browser passes**, plus two fresh-record repetitions of closure; lint, typecheck, locale checks and build passed. These are dated full-checkout results, not new clean-clone results. [Acceptance report](docs/FINAL_ACCEPTANCE_REPORT.md).

## Measured results and limitations

| Existing evidence | Result | Interpretation |
|---|---|---|
| V1 20-image live pilot | Precision 48.28%, recall 93.33%, F1 63.64%; safe-scene FP 42.86% | Small pilot, single primary reviewer, AI-assisted discussion, no secondary adjudication/electrical positives |
| Paired 10-image development comparison | V1 F1 58.33%, recall 100%; V2 F1 52.63%, recall 71.43%; FP 10 vs 7; FN 0 vs 2 | Reduced false positives with lost recall; not independent validation |
| Historical local retrieval | Recall@3 88.89%, no-answer accuracy 91.67%, unsupported citations 0% on 48 draft queries | Corpus-specific draft targets, not real-world legal correctness |
| Historical policy/workflow | 40/40 policy cases; 20/20 selected mocked workflow cases | Rule/service conformance, not recognition accuracy |

Read the [V1 run](evaluation/reports/vision_openai_sol_20_20260918_01/summary.md), [paired comparison](evaluation/reports/paired_live_20260919_step16/LIVE_COMPARISON.md), [error audit](docs/VISION_V2_PAIRED_ERROR_AUDIT.md) and [competition evidence](docs/FINAL_COMPETITION_CLAIMS.md). Cached live results and mocked acceptance tests are separate. Some older documents describe earlier pending states; prefer dated completed reports.

Publication copies redact local user paths and reviewer identities; labels, scoring, prompts and numerical results are preserved. Redacted hashes differ from original preserved audit hashes. Withheld photos prevent full historical visual reproduction from the proposed public package alone.

## License and publication status

No project-wide open-source license has been selected by the owner; no MIT/Apache grant is invented. Dependencies and external content retain their own licenses. Lockfiles are included; installed dependencies/model weights are excluded. See [third-party review](docs/THIRD_PARTY_MATERIALS.md).

The approved sanitized source is published at [JinzheLi-AI/SafeSite-Intelligence](https://github.com/JinzheLi-AI/SafeSite-Intelligence). This is a source-code repository, not a hosted application. Earlier publication-review documents retain their historical proposal wording. Keep credentials, private uploads, databases and traces out of Git. The offline `scripts/prepare_publication.py` prepares an audited proposal under ignored `.publication/`; it never uploads or calls a model. See [publication review](docs/PUBLICATION_REVIEW.md).
