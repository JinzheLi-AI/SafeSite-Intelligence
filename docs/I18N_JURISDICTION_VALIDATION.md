# English / Simplified Chinese and jurisdiction validation

Validated: 2026-09-15. Scope: existing SafeSite workflow, with bilingual presentation and project-context retrieval.

## Architecture and coverage

A lightweight React LocaleProvider supplies `t`, `locale`, and `setLocale`. Shared dictionaries live in `shared/locales/en.json` and `shared/locales/zh-CN.json` (711 entries each). The backend reads these same files for deterministic mock and Analyst presentation. No translation service or duplicated business workflow was added.

English is the initial default. The header EN | 中文 switch updates context immediately, sets the HTML language, and saves `safesite.locale` in localStorage. It preserves the current route and form state without reloading. On subsequent visits the saved language is restored after hydration. Storage-disabled browsers retain the selection for the current session only.

Coverage includes Dashboard, AI Inspection, Incidents, Incident Detail, AI Safety Analyst, Knowledge Base, navigation, shared controls, loading/error/empty states, form labels, risk and hazard badges, lifecycle statuses, mock evidence and recommendations, metric definitions and common answers. Internal enums, identifiers and database values remain language-independent. User-entered names, historical free-form records, technical SQL and official source titles retain their recorded text.

## AI output language

The client sends `X-SafeSite-Language: en|zh-CN`. Analyst requests may also specify a validated `language` body field. The provider dependency applies the request language to real and mock inspection/reinspection. Real prompts request localized narrative fields while preserving JSON keys, codes, numerical fields and English retrieval queries. Analysis provenance records output language. Existing records are not regenerated when the interface language changes.

The Analyst normalizes 16 common Chinese questions into the existing English interpreter and metric registry. All six required questions appear as suggestions. English and Chinese requests execute the same SQL and return identical raw rows and charts. Bilingual presentation fields allow existing deterministic answers to switch instantly. Flexible planning receives the preferred narrative language and retains all existing query validation.

## Official source policy

Official document titles, excerpts and stored source passages are unchanged. Citation cards label them **Official Source Text / 官方原文** and mark source passages `translate=no`. The dictionaries include **AI Explanation / AI 解读** for a separately identified explanation if supplied; this task adds no new explanation generator. Mock/sample sources remain explicitly distinct from verified evidence.

## Project jurisdiction and retrieval

Project now has `regulatory_jurisdiction`, default `HK-SAR`. Existing source metadata already had jurisdiction, so it is reused unchanged (`Hong Kong`). A small idempotent SQLite column addition upgrades existing projects without resetting rows. No broad migration or jurisdiction administration system was introduced.

Current verified pilot jurisdiction: **Hong Kong SAR**. Verified authority: **Hong Kong Labour Department**. Architecture: jurisdiction-aware and extensible. Mainland China (`CN`), Singapore (`SG`) and Malaysia (`MY`) appear as disabled Coming Soon options; they are not indexed or validated.

Knowledge search and real inspection retrieval resolve the actual project code, map it to corpus metadata, and filter verified active documents to that jurisdiction before ranking. Unknown, missing or unsupported project context returns unavailable with no citations; there is no Hong Kong fallback. Document listing uses the same project context. The UI hides results from a previously selected project while new context loads. The Dashboard clearly states that its metrics still cover all projects.

Future activation requires a reviewed source registry, verified documents, ingestion/quality validation, explicit corpus mapping and retrieval tests before enabling an option. No additional jurisdiction documents were ingested.

## Validation

- Backend: 229 passed (201 existing plus 28 new); two dependency deprecation warnings.
- New coverage: locale parity/domain labels, 16 bilingual metric equivalences, unsupported jurisdiction isolation, HK original-source retrieval, API project-context filtering, idempotent legacy upgrade, mock inspection/reinspection languages, real-provider prompt/contract and API language validation.
- Browser: **19 passed** (14 existing plus 5 new), 37.8 seconds, Chromium/Edge against the production build. Five new scenarios cover switching/persistence and preserved form state, all major Chinese pages at 1366/390 widths, Chinese inspection and incident detail, six Analyst suggestions, and untranslated official citations.
- Frontend lint, standalone typecheck and production build: **passed**. Locale checker: **passed**, checking all 711 entries per locale and every literal frontend `t()` key.
- Visual review: Chinese Dashboard, Analyst result and mobile Knowledge Base screenshots; navigation, badges, tables and charts remain readable. Official English source titles are intentionally preserved.
- RiskEngine, SQL safety policy and semantic metric registry hashes match the pre-task baseline.
- Existing test assertions remain intact. Analyst browser tests additionally wait for one settled streamed form before input. Knowledge fixture routing now lets the new context endpoint reach the API. The new disabled-option assertion checks the native `disabled` property.

## Limitations

No live paid model call was made for this change; real provider language instructions and structured contracts were tested with an injected SDK. Arbitrary historical AI narratives are not automatically translated. Deterministic Chinese Analyst support covers the registered common questions, not unrestricted Chinese language understanding. Dates retain the pilot's existing Hong Kong timezone semantics. Browser workflow tests create labeled demo records in the local application database. No new authentication, forecasting or jurisdiction corpus was added.

## Click paths

1. Open `http://127.0.0.1:3000/` -> header **中文** -> visit AI Inspection, Incidents, an incident detail, AI Safety Analyst and Knowledge Base -> refresh -> Chinese remains selected. Click **EN** to restore English. To confirm state preservation, type a location in AI Inspection before switching.
2. Open **Knowledge Base** -> **Regulatory Jurisdiction**: Hong Kong SAR is Active / Verified. Open the selector: Mainland China, Singapore and Malaysia are disabled Coming Soon options. Search verified guidance and inspect **Official Source Text**; switch language and confirm the quoted passage/title stay unchanged.
3. Open **AI Safety Analyst** -> 中文 -> select any of the six suggested questions -> inspect the translated result and Technical details. Raw SQL and underlying metric codes remain unchanged.

## Exact implementation file inventory

Generated database/runtime/cache/test-result files are excluded. The inventory below compares source files to the pre-task SHA-256 baseline.

- `README.md`
- `backend/app/ai/mock.py`
- `backend/app/ai/provider.py`
- `backend/app/ai/real.py`
- `backend/app/analyst/contracts.py`
- `backend/app/analyst/interpreter.py`
- `backend/app/analyst/localization.py`
- `backend/app/analyst/provider.py`
- `backend/app/analyst/service.py`
- `backend/app/api/analyst.py`
- `backend/app/api/knowledge.py`
- `backend/app/core/jurisdictions.py`
- `backend/app/core/localization.py`
- `backend/app/knowledge/retrieval.py`
- `backend/app/main.py`
- `backend/app/models/entities.py`
- `backend/app/schemas/contracts.py`
- `backend/app/services/workflow.py`
- `backend/tests/test_i18n_jurisdiction.py`
- `backend/tests/test_knowledge.py`
- `docs/I18N_JURISDICTION_VALIDATION.md`
- `frontend/e2e/analyst.spec.ts`
- `frontend/e2e/i18n.spec.ts`
- `frontend/e2e/knowledge.spec.ts`
- `frontend/package.json`
- `frontend/scripts/check-i18n.mjs`
- `frontend/src/app/analyst/page.tsx`
- `frontend/src/app/error.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/incidents/[id]/page.tsx`
- `frontend/src/app/incidents/page.tsx`
- `frontend/src/app/inspections/page.tsx`
- `frontend/src/app/knowledge/page.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/loading.tsx`
- `frontend/src/app/not-found.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/components/analysis-progress.tsx`
- `frontend/src/components/analysis-source.tsx`
- `frontend/src/components/analyst-result.tsx`
- `frontend/src/components/audit-timeline.tsx`
- `frontend/src/components/charts.tsx`
- `frontend/src/components/image-upload.tsx`
- `frontend/src/components/incident-detail.tsx`
- `frontend/src/components/incident-table.tsx`
- `frontend/src/components/inspection-form.tsx`
- `frontend/src/components/inspection-results.tsx`
- `frontend/src/components/jurisdiction-context.tsx`
- `frontend/src/components/reinspection-panel.tsx`
- `frontend/src/components/risk.tsx`
- `frontend/src/components/shell.tsx`
- `frontend/src/components/ui.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/i18n.tsx`
- `frontend/src/lib/project-context.tsx`
- `frontend/src/lib/types.ts`
- `frontend/src/lib/use-resource.ts`
- `shared/locales/en.json`
- `shared/locales/zh-CN.json`
