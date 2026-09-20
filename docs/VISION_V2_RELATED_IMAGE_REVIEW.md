# V2 source and related-image review

Completed 2026-09-19 using actual local images, historical contact sheet, ten archived Commons API records, manifest metadata and current validator. No network or model calls. Source contents were available locally; no replacement images downloaded.

## Decision

All ten relationship reviews completed. Only related_image_review_status changed from pending to reviewed. Sites/scene IDs, human labels, notes and judgments remain unchanged. The evaluation plan permits documented unknown identities and conservative grouping. Completion records the investigation, not certified independence. Existing development-only groups remain reserved against future held-out collection.

## Case findings

| Case | Source identifier | Site/scene, relatedness and evidence | Decision / remaining uncertainty |
|---|---|---|---|
| v2_development_001 | commons:pageid:28209761 | B versus 003: outdoor Peterburi tee reconstruction, Tallinn, 2013-09-08 versus Kivila 11 indoor apartment renovation, 2012-01-24. C versus 002: shared Dmitry G photographer; lamppost site unknown. Keep source-series reservation. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_002 | commons:pageid:17040673 | C: Dmitry G, 2011-10-19 lamppost wiring detail; distinct depicted subject from 001/003 but common physical site cannot be ruled out for 001. No location in archive. Keep unknown and shared reservation. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_003 | commons:pageid:18157020 | B versus 001: Kivila 11 interior apartment renovation, 2012-01-24, distinct location/context. C versus 002: photographer shared; 002 site unresolved. Keep reservation. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_004 | commons:pageid:141242382 | Archived description identifies Klinikum Osnabrueck, categories Finkenhuegel, Ramsch, 2023-11-21. Orange outdoor cabinet/trees visually distinct. No matching known site/source in other registered collections; unrecorded historical site relationships D. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_005 | commons:pageid:179025422 | B versus 009: archive explicitly says Makati/Greater Manila, 2017-12-07, high-rise facade; 009 is Banaue/Ifugao, 2017-11-26. Same Tupungato photographer, different documented locations. Exact building unknown; retain conservative shared reservation. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_006 | commons:pageid:6489578 | Thiemo Schuff, THW distribution equipment, 2007-10-07. Blue/white box on paving visually differs from 007 yellow box and 008 facade. Site unspecified; physical-site relationship D. Retain THW series reservation; archive notes derivative versions so future derivatives must be excluded. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_007 | commons:pageid:130047017 | Leo Miregalitheo, 2023, yellow portable distribution box on sheeting beside wall/paving. Different source and depicted scene from 008 (Patrick Oberdoerfer, 2017, multi-storey facade). B at visible scene level; common physical site D. Saved notes broadly match 007, copied into 008. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_008 | commons:pageid:138154067 | Patrick Oberdoerfer, 2017-09-28, description cable bridges for construction power. Actual image: scaffolded multi-storey facade, elevated cable-support structure, red/white KBS boxes, foreground flexible conduit. B versus 007 visible scene; common site D. Annotation notes incorrectly describe 007; correction requires user approval. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_009 | commons:pageid:134276899 | B versus 005: archive explicitly locates rooftop in Banaue/Ifugao, 2017-11-26, distinct from Makati high-rise dated 2017-12-07. Shared Tupungato author only; retain conservative series reservation. Exact building/site ID remains unknown. | reviewed; no cross-split match identified, unknown historical site relationships remain |
| v2_development_010 | commons:pageid:42037287 | USACE/Carol E. Davis, 2010-12-12, explicitly Tel Nof Air Base new dining facility. Interior stairs and worker; no matching registered source/site. Archive includes Flickr source ID 5307790955. Unrecorded historical site relationships D. | reviewed; no cross-split match identified, unknown historical site relationships remain |

A = confirmed same scene (none found among development pairs); B = confirmed different depicted scene or documented location as specified; C = shared photographer/series with scene relationship unknown; D = unresolved physical-site relationship. Different scenes do not necessarily mean different sites. 005/009 documented cities establish different sites; no new building IDs invented.

## Cross-split scope and evidence

Hashed 39 files across evaluation/fixtures, backend/uploads, backend/data, frontend/public and docs; zero development matches outside their own registered files. Historical pilot 20 images visually inspected side by side: no recognizable same scene/crop found. Historical source records mostly lack original IDs/site IDs, so same-site absence cannot be certified. Held-out contains zero images; no current held-out leakage. Other evaluation hazard slots contain no images; knowledge diagrams/UI screenshots are not independent scene datasets. Cached snapshots/renditions are exposure records, not held-out data.

Compared populated source URLs, platform/original IDs, known site/scene IDs and reserved groups across current manifests. No matching populated cross-split identifiers. Source-series relationships within development are allowed. Quarantine any future held-out candidate with a matching group or uncertain shared-site relationship; rerun review before held-out freeze.

Full per-source archived metadata paths and SHA-256 fingerprints, local inventory and validation are in evaluation/reports/related_review_20260919/review.json. Backup: evaluation/reports/related_review_20260919/vision_v2_development_v1.before.json.

## 007/008 notes: approval needed only for 008

007 notes describe the visible yellow portable box, sheeting and boards; the core scene description matches. 008 has identical text but shows no such yellow box or sheeting. It shows a scaffolded facade, red/white cabinets, overhead cable supports and flexible conduit on gravel/grass beside paving. Thus the copied rationale is demonstrably incorrect for 008. Hazard labels and rationale have not been overwritten.

Proposed replacement for case 008 evidence_notes (awaiting approval):

> A scaffolded multi-storey facade is visible with overhead cable-support structures and red-and-white cabinets behind temporary fencing. A flexible conduit loops on the gravel and grass beside the paved edge in the foreground. The photograph does not show the yellow portable distribution box on plastic sheeting described in the previous note. Whether the conduit obstructs a pedestrian route is not established by the image alone; the existing housekeeping judgment requires a case-specific supporting rationale.

This draft describes observations and uncertainty, not a replacement hazard label. The user need only approve/correct this note and confirm the existing housekeeping rationale for 008; no ten-image reannotation is needed.

## Validation and preservation

```json
{
  "total_cases": 10,
  "images_present": 10,
  "missing_images": 0,
  "reviewed": 10,
  "benchmark_ready": 10,
  "duplicate_images": 0,
  "errors": [],
  "warnings": [
    "v2_development_002: site unknown; independence cannot be guaranteed",
    "v2_development_005: site unknown; independence cannot be guaranteed",
    "v2_development_006: site unknown; independence cannot be guaranteed",
    "v2_development_007: site unknown; independence cannot be guaranteed",
    "v2_development_008: site unknown; independence cannot be guaranteed",
    "v2_development_009: site unknown; independence cannot be guaranteed"
  ],
  "frozen": false
}
```

Verified 97 protected project files unchanged, including held-out and historical evidence. Manifest diff limited to ten relationship status values. Validator/product code unchanged. Unknown sites 002/005/006/007/008/009 remain warnings; all scene IDs remain unknown.

Structural benchmark readiness is 10/10. A separate annotation-quality issue remains for 008: do not treat this mechanical count as resolution of its incorrect rationale. Resolve that single case before interpreting paired development results. No independent held-out claim is justified. No benchmark run.