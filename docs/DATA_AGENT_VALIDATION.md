# Safety Data Agent validation

Implemented and validated on 2026-09-14. The Analyst now queries the actual configured SQLite database. Common English questions use deterministic semantic queries without credentials; flexible phrasing can use an optional OpenAI structured planner. No live analyst model call was made because credentials were unavailable. Generated-SQL paths were tested with injected plans and a mocked SDK response, not presented as live AI validation.

## Knowledge index preflight

Read-only inspection found 9 active official sources, 875 stored passages, 383 eligible passages and exactly 383 nonempty vectors. Eligible passages missing vectors: **0**. Ineligible passages with vectors: **0**. The other 492 stored passages are intentionally excluded by the existing parser/index eligibility rules (including non-hazard text, page/section exclusions and difficult comparison tables). Ingestion assigns one vector to each eligible passage atomically. The knowledge architecture, manifest, chunks and retrieval implementation were not modified.

## Architecture and routing

Question -> narrow deterministic interpreter -> registered metric/filters/time range -> SQL compiler -> SQLGlot AST validator -> separate SQLite read-only connection -> result validation -> approved chart/table and deterministic explanation.

If the deterministic interpreter cannot account for the complete question, optional OpenAI planning proposes an AnalyticsPlan. The application supplies a curated two-view schema and registered metric definitions/templates, not the raw database schema or operational rows. The strict plan contains supported flag, interpretation, metric enum, dimensions, typed filters, period enum, SQL, visualization preference and explanation. The proposed SQL must pass the same validator. Within one read transaction, the application also executes the canonical registered metric query and compares column names, row ordering, counts, values and truncation. A mismatch is rejected with no numerical answer. This prevents a model from redefining a metric even with syntactically safe SQL.

The application generates the final interpretation and insight from the approved plan and returned rows; it does not display model-authored factual answers. Charts are selected deterministically according to verified result shape. The optional model's explanation and chart preference are proposals, not authority. There is no agent tool that executes SQL directly and no request body field accepting raw SQL.

## Approved data scope

The executor installs two code-owned TEMP views on its read-only connection. They are connection-local and never persisted in the operational database.

- safety_incidents: one row per incident, joined to its primary hazard, inspection location, site and project. Corrective actions are pre-aggregated per incident to prevent join fan-out. Exposes IDs, incident code, site/project names, location, hazard type, initial risk, current status, creation/closure timestamps and duration proxies.
- safety_hazards: one row per recorded hazard observation, joined to inspection, site and project. Exposes IDs, names/location, hazard type, initial risk, inspection status and creation timestamp.

The trusted views read selected columns from **projects, sites, inspections, hazards, incidents and corrective_actions**. Generated queries may access only the two views, not the underlying tables. Exact column allowlists and view SQL are in backend/app/analyst/schema.py. Audit payloads, actor/assignee identities, image paths, descriptions/notes, JSON payloads, citations, knowledge tables, AIExecution, configuration and SQLite system tables are not queryable. No new persistent database tables or engines were added.

## Semantic metric registry

Definitions live in backend/app/analyst/metrics.py. Time filters select records by creation timestamp; statuses are current, and risk scores/levels are initial recorded values. A historical creation cohort is not a reconstruction of historical status.

| Metric | Fixed definition |
| --- | --- |
| `total_incidents` | Count all incidents, including rejected records. |
| `open_incidents` | Count currently unresolved incidents: OPEN, UNDER_REVIEW, RECTIFICATION or REINSPECTION. |
| `critical_incidents` | Count currently unresolved incidents with initial CRITICAL risk. |
| `closed_incidents` | Count incidents currently CLOSED. |
| `closure_rate` | Currently CLOSED / all non-REJECTED incidents in the creation cohort, multiplied by 100. |
| `average_rectification_time` | Mean elapsed hours from earliest corrective-action creation to latest completion, only where every action has a completed timestamp. Excludes rejected incidents. This is an action-resolution duration proxy, not measured time actively working. |
| `hazard_count` | Count all recorded hazard observations, including unconfirmed or rejected inspections; not a count of confirmed incidents. |
| `hazard_distribution` | Count recorded hazard observations by hazard type, including unconfirmed/rejected inspections. |
| `incident_count_by_site` | Count non-rejected incidents by site, using current status and initial risk. |
| `incident_count_by_risk_level` | Count non-rejected incidents by initial risk level. |
| `recurring_hazard_count` | Extra incidents beyond the first occurrence of the same primary hazard type at the same site within the creation cohort. Excludes rejected incidents; a repeated observation is not proof of a recurring physical defect. |
| `critical_incident_rate` | Initial CRITICAL incidents / all non-rejected incidents in the creation cohort, multiplied by 100. |
| `average_risk_score` | Mean initial risk score of currently unresolved incidents; matches the dashboard population before rounding. |
| `unresolved_incident_count` | Count OPEN, UNDER_REVIEW, RECTIFICATION and REINSPECTION incidents; excludes CLOSED and REJECTED. |
| `unresolved_incident_rate` | Currently unresolved / all non-rejected incidents in the creation cohort, multiplied by 100. |
| `average_closure_time` | Mean hours from incident creation to human closure, only CLOSED incidents with valid timestamps. |
| `incident_volume` | Count non-rejected incidents by Hong Kong creation day; absent days have no recorded incidents. |
| `incident_list` | List non-rejected incidents with current status and initial risk; newest first. |

Closure rate's denominator is the non-rejected creation cohort, including both closed and unresolved incidents. A nonempty cohort with zero closed cases returns 0%; an empty denominator returns no-data. Total incident count intentionally includes rejected records, while grouped incident counts exclude them. Hazard observation counts include unconfirmed/rejected inspections, consistent with the existing dashboard hazard chart. These distinctions are shown in the result definition rather than silently conflated.

Average rectification time is **not time actively spent rectifying**: the available action timestamps support only an elapsed action-resolution proxy. All actions must be completed with valid timestamps. Invalid/missing durations are excluded. Average closure time is separately defined from incident creation to human closure. Recurrence counts extra incidents after the first within each site/type group; repeated observations do not establish that a physical defect recurred.

## SQL security model

SQLGlot 29.0.1 parses SQLite SQL into an AST. Validation requires exactly one SELECT over one approved view, approved columns and a small expression/function allowlist. It rejects raw tables, qualified databases, system tables, joins, subqueries, CTEs, unions, windows, offsets, unrestricted stars (COUNT(*) is allowed), unknown functions, comments, malformed SQL and multiple statements. Mutation/DDL, PRAGMA, ATTACH/DETACH, transactions, filesystem functions and extension loading cannot pass.

Limits: 12,000 SQL characters, 300 AST nodes, 16 output columns, bounded literals, positive LIMIT capped at 100 rows, 200 KB result size, a two-second execution deadline and one-million SQLite VM-step budget per query. A one-row lookahead detects truncation; the response states that only returned groups/rows are represented. No extrapolated total or full-dataset trend is inferred from truncated data.

SQLite opens the configured file with mode=ro, disables extension loading, creates only trusted connection-local views, enables query_only, then installs an authorizer that denies unauthorized operations/columns/functions. Both candidate and canonical query use the same read snapshot. The authorizer permits SQLite's columnless join/count optimization reads only for approved base tables; AST validation still prevents end-user queries over those raw tables. The executor validates SQL independently of the service caller. Tests also bypass the AST and authorizer separately to verify that the read-only connection cannot mutate the main database.

Query errors, interruption and oversized results return explicit errors and no synthetic answer. Connections close after each request. Analytics writes no operational records, audit rows or AIExecution records. Structured application logs record question, metric, deterministic/generated path, proposed SQL, validation, rows, latency, status and provider/model. Logs escape control characters and redact configured keys and sk-style tokens; SDK exception text and internal prompts are not logged. Log retention is the deployment's responsibility.

## Time handling

Application analytics time is Hong Kong time, UTC+08:00 (fixed offset, no DST). Supported periods: today, this week (Monday start), this month, rolling last 7 days, rolling last 30 days, previous calendar month and all available history up to now. Bounds convert to UTC for storage comparisons, start inclusive and end exclusive. Day grouping uses +8 hours. Unknown qualifiers are not silently discarded by the deterministic interpreter; unsupported phrases require a more precise question or the optional planner. Exact site/project filters can use `at site "Tower A"` or `for project "Harbour Residence Phase 2"`.

## Configuration and modes

Backend environment, then restart API:

```dotenv
SAFESITE_ANALYST_PROVIDER=deterministic
SAFESITE_ANALYST_MODEL=gpt-5.6-terra
SAFESITE_ANALYST_TIMEOUT_SECONDS=30
```

Deterministic mode queries real local data and requires no API key. It is the default and is explicitly labeled "Database query - no LLM" in the UI (the badge uses a middle dot separator). It is not fake analytics or mocked SQL.

For flexible natural-language planning set SAFESITE_ANALYST_PROVIDER=openai, configure an accessible structured-output text model using SAFESITE_ANALYST_MODEL, and set OPENAI_API_KEY on the backend. The analyst configuration is independent of the vision provider. Common questions still use the deterministic path even when OpenAI is configured. A flexible request with missing credentials returns unavailable; a model failure returns an error, without silent fallback. The SDK uses the official endpoint, store=false, a bounded timeout and no automatic retry.

Offline tests inject a deterministic planner or mocked SDK and label that path test; there is no production fake-model switch. POST /api/v1/analyst/query accepts only a question. GET /api/v1/analyst/capabilities reports provider readiness and metric definitions without returning credentials or prompts.

## Visualizations and UI

The existing Next.js design, panels and Recharts are retained. Approved output types are metric, bar, line and table. Pie/donut is deliberately omitted because no current question needs it. A single scalar uses a KPI; one small categorical grouping uses a bar chart; daily volume uses a line chart; multi-dimensional, large grouped and incident detail results use tables. Every successful answer also includes supporting database rows. Chart axis names and numeric values are validated against returned data; the model cannot supply frontend code.

The page includes all five requested suggestion cards, question input, a non-delayed analysis state listing the four real pipeline steps, direct answer, supporting KPI/chart/table, concise insight, canonical interpretation, metric definition, time range and assumptions. Technical details reveal validated SQL, metric, row count, latency and provider. Rejected, unsupported, no-data and unavailable states are explicit. Case closure remains human-only elsewhere in the application.

## Existing data and manual A-H validation

The starting database had **28 incidents and 30 hazards**, across three sites, all six hazard types and several lifecycle states. This was sufficient for meaningful comparisons and recurrence. No seed changes, reset, or new analytics demo records were needed. The read-only A-H check ran before browser workflow tests at:

2026-09-14T05:03:45.787618+00:00

The database contains both seeded demonstrations and previously created workflow/test records; actual database results are not claims that these are genuine field events. Browser lifecycle regression tests subsequently create their usual demo incidents, so later live values may differ from this timestamped snapshot.

| Case / question | Status and actual result | Rows |
| --- | --- | --- |
| A. What is our most common hazard this month? | success: Unprotected Edge: 7.00 observations, joint highest in the returned groups. | 6 |
| B. Which site has the most critical incidents? | success: Tower A (site #1): 1.00 incidents, highest in the returned groups. | 1 |
| C. What is our incident closure rate? | success: Closure Rate: 46.43 %. | 1 |
| D. Which hazards are recurring? | success: Tower A / Working At Height (site #1): 7.00 repeat incidents, highest in the returned groups. | 7 |
| E. What is the average rectification time? | success: Average Rectification Time: 33.23 hours. | 1 |
| F. Show critical incidents from the last 30 days. | success: Showing 8 matching incidents. | 8 |
| G. Delete all incidents. | rejected: Only read-only safety analytics questions are allowed. No operational records were changed. | 0 |
| H. What is the price of concrete? | unsupported: This question cannot currently be answered from SafeSite's approved safety analytics data. | 0 |

A has a tie: unprotected edge and working at height each have seven observations in the selected month. B measures **currently unresolved critical incidents**, not all historical critical incidents. C is 13 closed / 28 non-rejected incidents. D's leading group has eight occurrences, so seven repeat incidents. E averages the qualifying completed-action groups, including elapsed waiting/approval time. F lists eight non-rejected initial-critical incidents in the rolling 30-day cohort. G is rejected; H is unsupported.

The complete row sets, SQL, interpretation, timestamps and timings are in backend/data/analyst/manual-validation.json (local generated artifact). A full SQLite logical dump SHA-256 before and after all A-H requests was identical:

`b4c7a780dc78b4aa6150c93b876abaf30b58b097384cceedba9dea0e94add4c1`

This includes the malicious G request. No records were added, changed or deleted by the analytics requests.

## Automated and browser validation

- Backend: **201 passed** (132 existing + 69 new), with two existing dependency deprecation warnings. Tests require no paid or external HTTP calls.
- New functional coverage includes common hazard, critical by site, closure denominator, action-duration proxy, recurrence, time windows, observation/incident grain, charts, no-data, unsupported qualifiers, generated SELECT, mismatched generated metrics, model failures, API contracts, logging/redaction and repeated read-only requests.
- Adversarial question tests reject DELETE, DROP, instruction override/UPDATE, sqlite_master, ATTACH, writable_schema, statement injection and key requests; logical database dumps remain unchanged. AST tests also reject arbitrary functions, raw/hidden columns, CTEs, subqueries, UNION, JOIN, negative LIMIT, OFFSET and other unsupported operations. Independent read-only and authorizer tests block direct mutation attempts.
- Resource tests verify row truncation, maximum result size and query interruption without damaging subsequent reads.
- Frontend lint, typecheck and production build: passed. 
- Browser checks: **14 passed** (10 existing, with obsolete placeholder assertions updated, plus four new Analyst scenarios). All four Analyst browser scenarios passed again after final mobile table spacing and time-series wording fixes. Desktop and 390-pixel mobile results were visually inspected.

The existing placeholder-only browser assertions were updated to assert the actual result region and honest deterministic-provider badge. Knowledge demo preview checks and the existing human lifecycle assertions remain intact. Initial browser failures were test-selector issues (Next.js route announcer also has role=alert; a middle-dot string was corrupted while editing); both were corrected without weakening functional checks.

## Limitations and next work

This is a controlled safety analytics layer, not arbitrary SQL access. Deterministic routing supports the documented English patterns; broad paraphrases and unspecified qualifiers may be unsupported. Optional generated SQL must fit the single-view grammar and reproduce canonical metric results; safe but differently shaped SQL can be rejected. There is no multi-turn conversational memory, custom date interval, business forecasting, historical status reconstruction, Chinese-language quality validation or general BI exploration.

Read-only file-backed SQLite is required; in-memory databases and other engines are intentionally unsupported by this executor. Output is capped at 100 rows/groups. Site/project name filters are exact matches. There is no authentication or per-user data segregation; the scope is the existing local/trusted competition application. No raw schema/system tables or sensitive payloads are available to the planner.

Live model planning quality and live vision accuracy remain unvalidated because credentials were unavailable. Registry/result checks constrain factual output but cannot prove that every optional-model interpretation matches the user's intended question. The explicit interpretation and filters remain important for human review.

**Next:** run a small labeled live analyst evaluation with authorized credentials: paraphrases, ambiguous dates/site names, metric selection, unsafe prompts and schema/SQL rejection rates. Compare generated plans against the registered expectations and record latency/cost before widening the grammar. Separately validate the existing real vision provider with actual images. Improve rectification measurement only when trustworthy work-start/completion events are available; do not silently relabel the current proxy.

## Exact click path

1. Start backend and frontend using README. Default analyst provider needs no credentials.
2. Open http://127.0.0.1:3000/analyst or click AI Safety Analyst in the sidebar.
3. Click "What is our incident closure rate?" Review the KPI and denominator, then expand Technical details to inspect SQL and row count.
4. Click "What is our most common hazard this month?" Inspect the bar chart and matching supporting rows.
5. Click "Which hazards are recurring?" Review site/type groups, occurrence counts and the conservative definition.
6. Enter "Show critical incidents from the last 30 days." Inspect current status, initial risk and the displayed time range.
7. Enter "Delete all incidents." Confirm Request rejected. Enter "What is the price of concrete?" Confirm Question not supported.
8. Enter `What is our incident closure rate at site "No Such Site"?` to see the no-data state.
9. With optional OpenAI settings and credentials configured, restart backend and try a paraphrase such as "Break down incident totals per site for safety review". Inspect the AI-plan provider label, canonical interpretation and validated SQL. Without credentials this flexible path is explicitly unavailable; it was tested offline here.

## Exact files changed

Paths below are relative to safesite/. No RiskEngine, workflow service, seed or RAG implementation files were changed.

- `backend/app/analyst/__init__.py`
- `backend/app/analyst/contracts.py`
- `backend/app/analyst/schema.py`
- `backend/app/analyst/metrics.py`
- `backend/app/analyst/sql_safety.py`
- `backend/app/analyst/interpreter.py`
- `backend/app/analyst/provider.py`
- `backend/app/analyst/service.py`
- `backend/app/api/analyst.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env.example`
- `backend/requirements.txt`
- `backend/requirements.lock.txt`
- `backend/tests/test_analyst.py`
- `frontend/src/app/analyst/page.tsx`
- `frontend/src/components/analyst-result.tsx`
- `frontend/src/app/globals.css`
- `frontend/e2e/analyst.spec.ts`
- `frontend/e2e/workflow.spec.ts`
- `README.md`
- `docs/DATA_AGENT_VALIDATION.md`

## Implementation references

The optional planner follows the existing SDK pattern and official [OpenAI Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs). SQL validation uses the AST API described in the [SQLGlot documentation](https://sqlglot.com/). Application safety enforcement is implemented locally and does not rely on model compliance alone.
