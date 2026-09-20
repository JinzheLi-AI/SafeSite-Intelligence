# Verified safety guidance retrieval validation

Final index and manual queries checked 2026-09-13. Official source manifest reviewed 2026-09-12. Actual official PDFs were downloaded, parsed and embedded successfully. No paid embedding or vision calls were made. Live vision accuracy remains untested because credentials were unavailable.

SafeSite provides AI-assisted retrieval of official safety guidance. It is not legal advice and does not replace qualified safety professionals.

## Architecture and storage

The existing FastAPI/SQLAlchemy/SQLite application remains in place. Real vision hazard candidates pass through the unchanged deterministic RiskEngine, then hazard-aware retrieval, persisted citation evidence, and the existing human review workflow. Retrieval never determines risk or closes cases. Mock inspections retain explicitly unverified demo citations.

Three additive tables store official document revisions, extracted chunks with JSON vectors, and citation grounding snapshots linked to the existing RegulationCitation records. NumPy exact cosine scanning is appropriate for this compact corpus: 383 indexed vectors fit comfortably in memory without a separate vector service or database migration. Metadata and vectors persist in the configured SQLite database (default backend/data/safesite.db). Downloaded PDFs, receipts, the ingestion report and the model cache live under backend/data/knowledge/. These generated files are ignored by Git.

API startup creates the additive tables but does not download documents or models. A missing compatible index returns unavailable. Changing the embedding model requires ingestion for that model. Initial model download occurs only in the explicit ingestion CLI.

## Official corpus and source provenance

Only controlled entries in backend/app/knowledge/hk_core.json can be registered. All nine sources are Hong Kong Labour Department publications, jurisdiction Hong Kong. Source registration requires the reviewed URL and SHA-256; exact hashes, catalog links, page bounds and exclusions are in the manifest. The downloader checks the official catalog link and uses HTTPS on www.labour.gov.hk, disables redirects, restricts paths and rejects arbitrary URLs, oversized downloads, non-PDF responses and checksum changes. Limits are 30 MB, 45 seconds HTTP timeout and 90 seconds stream duration. PDF content is parsed as data, never executed.

Official catalogs: [guides and handbooks](https://www.labour.gov.hk/eng/public/content2_8d.htm), [guidance notes](https://www.labour.gov.hk/eng/public/content2_8c.htm), [codes of practice](https://www.labour.gov.hk/eng/public/content2_8b.htm).

| Official source | Type | Version | Effective date | Stored / indexed chunks |
| --- | --- | --- | --- | --- |
| [Overview of Work-at-Height Safety](https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf) | safety_guide | Second edition, February 2023 | Unknown | 76 / 36 |
| [Safety Handbook for Construction Site Workers](https://www.labour.gov.hk/eng/public/os/D/ConstrutionSite.pdf) | handbook | Not specified | Unknown | 44 / 19 |
| [Work Safety - Electrical Safety and You](https://www.labour.gov.hk/eng/public/os/D/Work_Safety_Electrical_Safety_and_You.pdf) | safety_guide | Not specified | Unknown | 20 / 10 |
| [Guidance Notes on the Selection, Use and Maintenance of Safety Helmets](https://www.labour.gov.hk/eng/public/os/C/GN_on_helmet_eng.pdf) | guidance_note | Third edition, June 2018 | Unknown | 59 / 31 |
| [Corrigendum to the Guidance Notes on the Selection, Use and Maintenance of Safety Helmets (3rd edition)](https://www.labour.gov.hk/eng/public/os/C/Corrigendum_to_GN_Safety_Helmet_eng.pdf) | guidance_note | 23 September 2019 | Unknown | 5 / 0 |
| [Code of Practice for Metal Scaffolding Safety](https://www.labour.gov.hk/eng/public/os/B/mss.pdf) | code_of_practice | Second edition, March 2013 | Unknown | 372 / 157 |
| [Code of Practice for Metal Scaffolding Safety - Addendum No. 1/2026](https://www.labour.gov.hk/eng/public/pdf/os/B/Addendum%20No.%201_2026%20MSS_TC.pdf) | code_of_practice | Addendum No. 1/2026 | 2026-07-31 | 8 / 3 |
| [Code of Practice for Bamboo Scaffolding Safety](https://www.labour.gov.hk/eng/public/os/B/Bamboo.pdf) | code_of_practice | Fifth edition, April 2024 | Unknown | 283 / 124 |
| [Code of Practice for Bamboo Scaffolding Safety - Addendum No. 1/2026](https://www.labour.gov.hk/eng/public/pdf/os/B/Addendum%20No.%201_2026%20BSS_TC.pdf) | code_of_practice | Addendum No. 1/2026 | 2026-07-31 | 8 / 3 |

Total: **9 active documents, 875 stored chunks, 383 indexed vectors**. Stored chunks include passages excluded from retrieval. The database also retains 45 inactive document revisions from parser development (54 revisions total); these are not additional distinct sources and are excluded from current search. An unchanged rerun reported all nine sources unchanged without duplicating chunks.

The corpus contains four code-of-practice documents including addenda, two guidance-note documents including the corrigendum, two safety guides and one handbook. Contracts also support legislation and official alerts, but neither is ingested here. These publications are not all legislation.

## Extraction, chunking and metadata

PyMuPDF 1.28.2 extracts native text; there is no OCR fallback. Parser hk-sections-v5 groups numbered clauses, short headings and paragraphs, aiming for about 1,400 characters. Oversized passages above 2,200 characters are excluded rather than truncated into misleading evidence. Physical PDF page numbers are one-based and may differ from printed page labels. Hierarchical clause numbers are retained where available; unnumbered passages use a PDF-page label, without inventing a section number.

Document-specific reading order handles handbook panels and electrical leaflet columns. Reviewed page ranges exclude covers, contents, bibliography, contact pages and complex tables. Hazard concepts tag relevant paragraphs for six supported categories. Exclusions and extraction concerns are recorded as quality notes. No extracted clauses are hardcoded in Python.

Document metadata includes title, authority, jurisdiction, document type, official URL, catalog URL, nullable publication/effective dates and version, language, verification and active flags, related-source key, checksum, parser/model signatures and retrieval/ingestion timestamps. Chunks retain document ID, ordinal, section, heading, physical page, original text, hazard categories, vector and active status. Citation contracts join that metadata and include chunk ID, excerpt, scores and the exact source URL.

## Embeddings, retrieval and reranking

Default: FastEmbed 0.8.0 with BAAI/bge-small-en-v1.5, running locally using ONNX Runtime. No API key is required. OpenAI embeddings are optional and configurable; missing credentials produce an explicit error without substituting demo evidence.

Queries are whitespace-normalized and expanded with hazard concepts and synonyms. Retrieval first filters Hong Kong, active/verified documents, matching model signatures and reviewed registry URLs/versions/checksums, effective dates and hazard categories. Base documents require their registered current amendments to be present. Candidate vectors are compared using cosine similarity, then reranked using 0.75 semantic similarity + 0.20 lexical overlap + 0.05 clause specificity. Deterministic penalties demote generic introductions, dangling introductory fragments, unrelated dismantling context and helmet-only text for edge/fall queries without helmet context.

Both semantic similarity and final score must reach 0.55, with actual query-term support. Near-duplicates above 0.80 token Jaccard similarity are removed; at most two results per document and three per hazard are returned. Scores are ranking heuristics, not calibrated confidence or legal applicability probabilities. Below threshold the response is: "No sufficiently relevant verified safety source was retrieved." No LLM fills the gap.

## Citation grounding and workflow resilience

There is no LLM explanation stage. Titles, section/page labels, excerpts, URLs and versions come exclusively from stored documents/chunks. Before persistence, evidence fields are compared again against the active database source and chunk. The existing citation row receives an immutable grounding snapshot and chunk link. Old demo rows remain demo/unverified; a bare legacy citation cannot become verified without grounding.

Real inspections retrieve after deterministic risk evaluation. Retrieval runs inside a savepoint so failures cannot discard hazard/risk results or block human confirmation. SAFETY_GUIDANCE_RETRIEVAL audit records capture query, hazard, candidate count, selected chunk IDs, scores, latency and status. Missing evidence and errors remain visible. RiskEngine scoring, human confirmation and human-only closure are unchanged.

## Versions and addenda

Checksums, model signature and parser/manifest signature identify revisions. New revisions deactivate previous ones atomically, preserving old chunks and citation snapshots. Rebuilding the same revision updates vectors without duplicating chunks. Unknown dates remain null rather than guessed.

Metal and bamboo addenda No. 1/2026 are linked to their base codes and effective 2026-07-31. The manifest conservatively excludes affected parent sections and Appendix III from the older base text. The helmet corrigendum is linked and stored, but its old/new comparison table is not vector-indexed; the affected base section 3.1 is also excluded. This avoids presenting superseded wording at the cost of recall. There is no automatic legal consolidation or complete temporal reasoning engine. Future publisher changes require review and manifest updates; pinned checksums deliberately reject changed PDFs.

## Manual A-E retrieval results

These queries used actual downloaded PDFs and real local embeddings on the final index. This is a small qualitative check, not a benchmark. Scores below are final reranking scores. Latencies are single observations including model initialization for A, not performance guarantees.

### A: worker near exposed edge without visible fall protection

Hazard: `working_at_height`. Status: `success`. Latency: 2400 ms.

| Source | Section / physical PDF page | Score | Relevance judgment |
| --- | --- | --- | --- |
| [Overview of Work-at-Height Safety](https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf#page=25) | 6.2.1 / 25 | 0.664736 | Relevant fall-arrest guidance, but conditional on a working platform being impracticable; preserve this context. |
| [Overview of Work-at-Height Safety](https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf#page=5) | 2.4 / 5 | 0.659287 | Relevant general fall-prevention guidance; broader than the observed edge. |
| [Code of Practice for Bamboo Scaffolding Safety](https://www.labour.gov.hk/eng/public/os/B/Bamboo.pdf#page=23) | 4.4.1 / 23 | 0.650436 | Relevant guardrail/toeboard passage with scaffold-specific applicability. |

### B: construction worker without visible safety helmet

Hazard: `missing_ppe`. Status: `success`. Latency: 79 ms.

| Source | Section / physical PDF page | Score | Relevance judgment |
| --- | --- | --- | --- |
| [Guidance Notes on the Selection, Use and Maintenance of Safety Helmets](https://www.labour.gov.hk/eng/public/os/C/GN_on_helmet_eng.pdf#page=17) | 6.1 / 17 | 0.825430 | Relevant helmet selection guidance, but broader than the missing-helmet observation. |
| [Guidance Notes on the Selection, Use and Maintenance of Safety Helmets](https://www.labour.gov.hk/eng/public/os/C/GN_on_helmet_eng.pdf#page=21) | 7.1 / 21 | 0.813147 | Relevant helmet provision where head injury is foreseeable. |
| [Safety Handbook for Construction Site Workers](https://www.labour.gov.hk/eng/public/os/D/ConstrutionSite.pdf#page=16) | PDF page 16 / 16 | 0.765139 | Directly relevant advice to wear a safety helmet. |

### C: unsafe metal or bamboo scaffold working platform

Hazard: `unsafe_scaffolding`. Status: `success`. Latency: 132 ms.

| Source | Section / physical PDF page | Score | Relevance judgment |
| --- | --- | --- | --- |
| [Overview of Work-at-Height Safety](https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf#page=15) | 5.3.1 / 15 | 0.813754 | Relevant bamboo platform planking, but includes a dated contract condition requiring review. |
| [Code of Practice for Bamboo Scaffolding Safety](https://www.labour.gov.hk/eng/public/os/B/Bamboo.pdf#page=24) | 4.4.1 / 24 | 0.810016 | Relevant working-platform/planking requirements. |
| [Overview of Work-at-Height Safety](https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf#page=16) | 5.4.1 / 16 | 0.809405 | Relevant metal scaffold design, loading and access context. |

### D: exposed or unsafe electrical equipment on construction site

Hazard: `electrical_hazard`. Status: `success`. Latency: 71 ms.

| Source | Section / physical PDF page | Score | Relevance judgment |
| --- | --- | --- | --- |
| [Work Safety - Electrical Safety and You](https://www.labour.gov.hk/eng/public/os/D/Work_Safety_Electrical_Safety_and_You.pdf#page=2) | PDF page 2 / 2 | 0.812090 | Relevant equipment protection and wet/outdoor electrical risks. |
| [Work Safety - Electrical Safety and You](https://www.labour.gov.hk/eng/public/os/D/Work_Safety_Electrical_Safety_and_You.pdf#page=3) | PDF page 3 / 3 | 0.772670 | Relevant equipment, cords and earthing guidance. |
| [Safety Handbook for Construction Site Workers](https://www.labour.gov.hk/eng/public/os/D/ConstrutionSite.pdf#page=5) | PDF page 5 / 5 | 0.649720 | Relevant but broad workplace electrical checks; weaker specificity. |

### E: blocked access route and poor site housekeeping

Hazard: `housekeeping`. Status: `success`. Latency: 72 ms.

| Source | Section / physical PDF page | Score | Relevance judgment |
| --- | --- | --- | --- |
| [Safety Handbook for Construction Site Workers](https://www.labour.gov.hk/eng/public/os/D/ConstrutionSite.pdf#page=5) | PDF page 5 / 5 | 0.582302 | Relevant tidy workplace, clear passages and rubbish removal. Only one passage passed the threshold; coverage is limited. |

### Negative: tomato soup recipe astronomy galaxies

Hazard: `housekeeping`. Status: `no_match`. Latency: 72 ms.

No citation returned, as expected for this unrelated query.

## Parsing problems and remaining limitations

All nine downloads and document ingestions succeeded, but some content is deliberately not searchable. Initial retrieval exposed bibliography/heading-only matches, interleaved handbook panels, interleaved electrical columns, dropped short continuations and list numbers misidentified as sections. Those issues were corrected in parser v5 and covered with targeted fixtures. Malformed joined-word lines are excluded without discarding adjacent readable paragraphs. The complex height annex table is excluded. The helmet correction comparison table has five stored passages and zero indexed vectors; its amended base section is excluded. These are explicit coverage gaps, not successful retrieval of those sections.

Final A-E results have no obvious unrelated top match, but A and C require contextual/conditional interpretation, B initially favors broader helmet guidance, D includes a broad third result, and E is weakly covered with one result near the threshold. English-oriented embeddings and English primary documents do not establish Chinese-language retrieval quality. Scanned PDFs fail clearly without OCR. Broader PPE subtypes, unusual site conditions and adversarial/ambiguous queries need further evaluation. Manual validation does not establish legal completeness, production reliability or live vision accuracy.

## Checks completed

- Backend: **132 passed**, including 35 added knowledge tests and all 97 existing tests; two existing deprecation warnings.
- Browser: **10 passed**, including all seven existing scenarios and three knowledge scenarios. The existing library assertion now counts three demo cards specifically because nine official cards are also present; other workflow assertions remain intact.
- Frontend: lint, TypeScript typecheck and production build all passed.
- Automated knowledge tests use deterministic local fixtures without network or paid calls. They cover ingestion idempotency, source registration and metadata, hazard filters, all required query families, thresholds, citation limits/grounding, stale versions, failure isolation and preserved risk/human controls.
- Actual local UI check: nine official documents and three retrieved citations for "fall protection exposed slab edge". Screenshot: frontend/test-results/actual-hk-knowledge.png.
- CLI ingestion and unchanged rerun completed. Final machine-readable query results: backend/data/knowledge/manual-results.json. Ingestion report: backend/data/knowledge/sources/ingestion-report.json.
- No live vision inspection was run. Real-workflow citation integration is covered by deterministic tests; end-to-end live vision accuracy remains pending credentials.

## Reproduce and exact click path

From backend, with dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m app.knowledge.ingest --source-set hk_core
.\.venv\Scripts\python.exe -m app.knowledge.ingest --source-set hk_core --rebuild
# After PDFs, receipts and model have been cached:
.\.venv\Scripts\python.exe -m app.knowledge.ingest --source-set hk_core --offline
```

Use --offline --rebuild to rebuild from cached sources. The default directories are relative to the backend working directory. See README for all environment settings and server commands.

1. Start API on port 8000 and frontend on port 3000. Open http://127.0.0.1:3000/knowledge.
2. Inspect official document cards, source type, version/effective date, verification badge, active status, quality notes and chunk counts. The three demo records remain unverified.
3. Under Search verified sources, select Working at height, enter "fall protection exposed slab edge", and run search. Inspect the returned citation cards, expand Read stored passage and open the official PDF source link at its physical page.
4. To test an inspection with real vision, configure SAFESITE_AI_PROVIDER=real and a valid backend OPENAI_API_KEY and image-capable vision model, then restart the API. This step requires credentials and was not executed here.
5. Open AI Inspection, verify the real provider label, upload an actual site image and click Analyze Site. For detected supported hazards with qualifying matches, inspect VERIFIED SOURCE cards in Applicable Safety Guidance. Zero hazards or no qualifying citation is valid; there is no demo fallback.
6. Review the risk and evidence, confirm findings as a human, open the resulting incident and inspect the same persisted guidance. Case closure remains a separate human action. Search does not retroactively add citations to older inspections.

## Exact files changed in this task

Paths are relative to safesite/. Historical vision implementation/validation reports were not changed.

- `backend/app/knowledge/__init__.py`
- `backend/app/knowledge/hk_core.json`
- `backend/app/knowledge/contracts.py`
- `backend/app/knowledge/models.py`
- `backend/app/knowledge/registry.py`
- `backend/app/knowledge/concepts.py`
- `backend/app/knowledge/download.py`
- `backend/app/knowledge/embeddings.py`
- `backend/app/knowledge/chunking.py`
- `backend/app/knowledge/ingest.py`
- `backend/app/knowledge/retrieval.py`
- `backend/app/api/knowledge.py`
- `frontend/src/app/knowledge/page.tsx`
- `backend/tests/test_knowledge.py`
- `frontend/e2e/knowledge.spec.ts`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/api/overview.py`
- `backend/app/services/workflow.py`
- `backend/app/repositories/queries.py`
- `backend/app/schemas/contracts.py`
- `backend/requirements.txt`
- `backend/requirements.lock.txt`
- `backend/.env.example`
- `frontend/src/lib/types.ts`
- `frontend/src/components/risk.tsx`
- `frontend/src/components/incident-detail.tsx`
- `frontend/src/app/inspections/page.tsx`
- `frontend/e2e/workflow.spec.ts`
- `README.md`
- `docs/RAG_VALIDATION.md`
