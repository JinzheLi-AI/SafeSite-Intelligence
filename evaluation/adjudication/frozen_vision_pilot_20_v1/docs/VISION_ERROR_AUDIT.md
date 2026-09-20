# Offline Vision Evaluation Error Audit

Date: 2026-09-18. Run: `vision_openai_sol_20_20260918_01`. No paid or external API/model calls were made. This is an audit of cached evidence and code, not new inference, independent visual adjudication or automatic relabeling. Model descriptions below are claims, not independently verified photographic facts.

## Evidence and method

Read raw_results.json, metrics.json, case_errors.json and summary.md in the run directory; compared the current manifest with the frozen snapshot (identical); inspected docs/VISION_LABELING_GUIDE.md, backend/app/ai/prompts.py, backend/app/ai/sanity.py and the analyze_inspection review expression in backend/app/ai/real.py. Replayed only the pure review_notes function and Boolean review conditions against all 20 cached structured outputs; no provider/client was constructed. All 20 replayed flags match cached production results.
Benchmark totals remain unchanged: 14 true-positive labels, 15 false-positive labels, one false-negative label; micro precision 48.28%, recall 93.33%, F1 63.64%; safe-scene FP 3/7; unnecessary review 9/12. Errors are measured against the frozen primary-reviewer labels, not adjudicated truth.

## Main diagnosis

1. The prompt says to retain potentially relevant low-confidence findings and use possible/not-visible wording. Such wording qualifies the prose but does not remove the positive class. The classifier scores every hazard entry. This conflicts with the human guide's threshold of a supported hazard, particularly when the PPE requirement is unknown.
2. The prompt forbids assuming absent occluded PPE, yet also asks to name PPE that appears absent/not visible. It lacks an explicit two-part gate for visibly absent AND contextually required PPE. Cases 001/002/011/013 demonstrate unsupported positive decisions even in the model's own account.
3. There are incomplete class boundaries: elevation versus uncontrolled fall hazard, ordinary stored/working materials versus obstruction, and electrical objects versus visible unsafe electrical conditions. The model tends to retain possibilities while the reviewer often rejects them.
4. Human-review evaluation mixes uncertainty review with operational confirmation. The provider forces review for every hazard; the annotations sometimes expect no review for clear hazards. Generic limitations also trigger model ambiguity, so lowering a confidence threshold alone cannot explain or resolve the pattern.
5. Ground truth is not fully internally consistent. Some false positives and the only false negative warrant human adjudication rather than automatic model blame.

## Complete false-positive label audit

Triage definitions: clear model error = decision conflicts with the written rule given the model's own stated uncertainty, not proof of actual site safety; ambiguous = cached evidence cannot settle the class; potentially inconsistent ground truth = a plausible omission or inconsistent threshold merits human review. These are provisional audit categories. Counts: {'Clear model error relative to labeling rule': 5, 'Potentially inconsistent ground truth': 5, 'Ambiguous visual evidence': 5}.

### 1. case_001 ? missing_ppe

- Ground truth: `[]`; prediction: `['missing_ppe']`.
- Model description: Neither worker appears to be wearing eye protection. The image does not establish whether their current task or location requires it.
- Model visual evidence: Both workers' eyes are visibly uncovered. | Clear safety glasses are hanging from the male worker's clothing rather than being worn. | The workers are positioned in a construction-site setting, but the immediate activity appears to involve a clipboard and handheld device.
- Human notes: Two workers are visibly wearing hard hats, and one worker is also wearing a high-visibility vest. No exposed edge, unsafe scaffolding condition, electrical hazard, obstructed access route, or other supported hazard can be confidently identified from the visible scene.
- Assessment: **Clear model error relative to labeling rule**. The model explicitly says the eye-protection requirement is unknown but still emits a positive hazard. Visible uncovered eyes do not establish a required-PPE violation.
- Human label review warranted: No specific label defect; review protocol only.

### 2. case_002 ? missing_ppe

- Ground truth: `[]`; prediction: `['missing_ppe']`.
- Model description: Safety glasses or other eye protection are not visible on the two foreground workers while they appear to be handling reinforcing steel. The workers' downward-facing positions and helmet brims partially obscure their faces, so absence cannot be confirmed from this image alone.
- Model visual evidence: Both foreground workers are visibly wearing yellow hard hats, high-visibility vests, and work gloves. | No safety glasses or goggles are visible on the portions of either worker's face shown. | The left worker's face is shaded and partly obscured by the hard-hat brim; the right worker is looking downward.
- Human notes: Two workers are wearing hard hats and high-visibility vests while working around reinforcement steel. No exposed edge, fall-from-height condition, unsafe scaffold, electrical hazard, or obstructed access route can be confidently identified from the visible scene.
- Assessment: **Clear model error relative to labeling rule**. The model explicitly cannot confirm absence because of facial occlusion; it nevertheless labels missing eyewear. Its separate out-of-category rebar concern can explain review without justifying this class.
- Human label review warranted: Review expected-review scope for the rebar concern; do not infer a PPE-positive label.

### 3. case_003 ? working_at_height

- Ground truth: `['missing_ppe']`; prediction: `['missing_ppe', 'working_at_height']`.
- Model description: The workers are standing beside a visibly elevated perimeter overlooking terrain and buildings below. A multi-rail metal barrier is present, but the image does not establish its dimensions, condition, or compliance.
- Model visual evidence: A distant cityscape and buildings far below are visible beyond the workers, indicating an elevated location. | Both foreground workers are positioned immediately beside a horizontal metal perimeter railing. | Multiple horizontal rail members are visible along the open side.
- Human notes: Two workers are standing in an elevated construction-area environment while holding hard hats rather than wearing them. Their heads are clearly visible and uncovered. A guardrail is present along the edge, so the image does not clearly support an unprotected-edge hazard. The scene is elevated, but the visible guardrail reduces the evidence for an immediate fall-exposure condition.
- Assessment: **Potentially inconsistent ground truth**. The reviewer excludes height because a guardrail reduces immediate exposure, whereas 009/011/012 label elevated work despite visible rails and unknown protection details. The ontology mixes elevated work with uncontrolled fall hazard.
- Human label review warranted: Yes: align 003 with 009/011/012/015/019/020 under a single definition.

### 4. case_004 ? housekeeping

- Ground truth: `['working_at_height', 'unprotected_edge']`; prediction: `['housekeeping', 'missing_ppe', 'unprotected_edge', 'working_at_height']`.
- Model description: Bricks and long boxed or board-like materials are stored near the low exterior boundary, creating a possible displacement or falling-object concern.
- Model visual evidence: Multiple stacks of loose bricks are positioned near the front opening. | Long boxed or board-like materials are leaning beside the low concrete boundary on the right. | The stored materials are adjacent to an occupied work and access area.
- Human notes: Workers are positioned at an elevated building opening close to the exterior edge. The visible edge protection appears limited to a low concrete upstand rather than a complete guardrail system. The scene supports possible fall exposure, although the exact working height and complete protection arrangement cannot be fully confirmed from this image.
- Assessment: **Ambiguous visual evidence**. Stored materials near an edge are converted to a displacement/falling-object concern without clearly establishing obstructed access or unsafe storage. Falling objects and housekeeping are not automatically equivalent.
- Human label review warranted: Yes: decide whether actual unsafe accumulation/access obstruction is visible, rather than ordinary storage.

### 5. case_004 ? missing_ppe

- Ground truth: `['working_at_height', 'unprotected_edge']`; prediction: `['housekeeping', 'missing_ppe', 'unprotected_edge', 'working_at_height']`.
- Model description: One worker inside the construction area has a clearly visible uncovered head while nearby workers are wearing hard hats.
- Model visual evidence: The standing worker near the center has visible hair and no hard hat on the head. | The worker is wearing a high-visibility vest and is positioned among scaffolding and stored masonry materials. | Three nearby workers are visibly wearing hard hats.
- Human notes: Workers are positioned at an elevated building opening close to the exterior edge. The visible edge protection appears limited to a low concrete upstand rather than a complete guardrail system. The scene supports possible fall exposure, although the exact working height and complete protection arrangement cannot be fully confirmed from this image.
- Assessment: **Potentially inconsistent ground truth**. Model evidence describes a clearly uncovered head among other helmeted workers. Human notes focus on fall exposure and do not address this worker. Possible omission, not established visual truth.
- Human label review warranted: Yes: inspect the original for headwear and contextual requirement; compare 003/014.

### 6. case_007 ? housekeeping

- Ground truth: `['missing_ppe']`; prediction: `['housekeeping', 'unprotected_edge']`.
- Model description: The immediate work surface contains a raised loop of reinforcing steel, loose concrete debris, and a cable, creating possible contact or trip hazards.
- Model visual evidence: A loop of reinforcing steel projects upward from the concrete directly in front of the worker. | Loose concrete fragments and uneven broken surfaces are visible around the worker's hands and knees. | A dark cable lies across the foreground work surface.
- Human notes: The worker is wearing a hard hat, face covering and gloves, but no high-visibility vest is visible. The image does not establish whether a high-visibility garment is required for this specific task or work zone, so the PPE finding should be treated as uncertain and subject to human review.
- Assessment: **Ambiguous visual evidence**. A work surface with debris, raised rebar and a cable may present contact risk, but the record does not establish an obstructed walking route. Human notes discuss PPE only.
- Human label review warranted: Yes: check the actual route and distinguish active work debris from a clear trip obstruction.

### 7. case_007 ? unprotected_edge

- Ground truth: `['missing_ppe']`; prediction: `['housekeeping', 'unprotected_edge']`.
- Model description: A dark recess bordered by concrete is visible at the lower right and may be an uncovered slab opening. The image does not show enough of the area to establish its depth or fall potential.
- Model visual evidence: A concrete edge borders a dark recessed area at the lower-right side of the image. | No cover or guard is visible over the portion of the possible opening shown in the frame. | The worker is positioned near the visible edge, although the exact distance is unclear.
- Human notes: The worker is wearing a hard hat, face covering and gloves, but no high-visibility vest is visible. The image does not establish whether a high-visibility garment is required for this specific task or work zone, so the PPE finding should be treated as uncertain and subject to human review.
- Assessment: **Ambiguous visual evidence**. Model describes a possible opening with unknown depth and explicitly cannot establish fall potential. This falls below the guide's proof threshold for an elevated/open edge.
- Human label review warranted: Yes: resolve opening/depth; retain uncertainty if not resolvable, without assuming a positive hazard.

### 8. case_011 ? housekeeping

- Ground truth: `['working_at_height']`; prediction: `['housekeeping', 'missing_ppe', 'working_at_height']`.
- Model description: Coiled cables and several loose lines are draped over or attached around the platform framing, presenting possible snagging, entanglement, or trip concerns.
- Model visual evidence: A large coil of dark cable hangs near the center of the platform. | Multiple cables or hoses run along and across the platform guardrail area. | Several loose rope ends and loops hang from the right side and center of the platform.
- Human notes: Workers are visibly operating on a suspended exterior work platform at significant elevation. The platform has visible guardrails, but the image does not clearly show the workers’ fall-arrest attachment or the full condition of the suspension system. The scene clearly supports work-at-height exposure and warrants human review of the protection arrangements.
- Assessment: **Ambiguous visual evidence**. Suspension-platform lines and a coil are interpreted as trip/entanglement hazards without showing the walking surface obstruction. Necessary working lines are not automatically unsafe clutter.
- Human label review warranted: Yes: distinguish operating/suspension lines from avoidable obstruction or snag exposure.

### 9. case_011 ? missing_ppe

- Ground truth: `['working_at_height']`; prediction: `['housekeeping', 'missing_ppe', 'working_at_height']`.
- Model description: A clearly identifiable safety helmet is not visible on the worker; dark headwear or image distance makes this observation uncertain.
- Model visual evidence: The worker's head is visible, but the dark covering does not have clearly distinguishable hard-hat features. | Image distance and shadows obscure the exact type of headwear.
- Human notes: Workers are visibly operating on a suspended exterior work platform at significant elevation. The platform has visible guardrails, but the image does not clearly show the workers’ fall-arrest attachment or the full condition of the suspension system. The scene clearly supports work-at-height exposure and warrants human review of the protection arrangements.
- Assessment: **Clear model error relative to labeling rule**. Model acknowledges shadows/distance prevent identifying headwear. It converts inability to identify a helmet into a positive missing-PPE class.
- Human label review warranted: No established label defect; optional image adjudication cannot manufacture unseen detail.

### 10. case_013 ? missing_ppe

- Ground truth: `[]`; prediction: `['missing_ppe']`.
- Model description: The worker appears to be manipulating tubing or conduit with bare hands. Gloves are not visible, although the task-specific need for gloves cannot be determined from the image alone.
- Model visual evidence: The worker's left hand is visibly gripping red tubing or conduit without a glove. | The worker's right hand is also visibly bare against the masonry surface. | A yellow hard hat and clear safety glasses are visibly worn.
- Human notes: The worker is visibly wearing a hard hat and safety glasses. The visible red cable or hose does not by itself establish an electrical hazard, and no fall, edge, scaffolding, or housekeeping hazard can be confidently identified from the scene.
- Assessment: **Clear model error relative to labeling rule**. Bare hands are observed, but the model explicitly cannot determine the need for gloves. Positive classification conflicts with the guide's task-context requirement.
- Human label review warranted: No specific label defect; compare uncertain PPE treatment with case_007.

### 11. case_014 ? housekeeping

- Ground truth: `['missing_ppe']`; prediction: `['housekeeping', 'missing_ppe']`.
- Model description: A long cable or hose and a large coil are positioned at the worker's feet on rough, debris-covered ground, creating a possible trip or entanglement hazard.
- Model visual evidence: A cable or hose extends across the ground directly in front of and beside the worker's boots. | The worker is holding a large coil with loops hanging near knee and foot level. | The walking surface is visibly uneven and contains loose rocks and soil.
- Human notes: The worker is standing in an active construction/excavation area with his head fully visible and no hard hat being worn. No clear evidence supports a working-at-height, unprotected-edge, scaffolding, electrical, or housekeeping hazard in this image.
- Assessment: **Potentially inconsistent ground truth**. Model describes a hose at boots and loops near foot level; human notes explicitly reject housekeeping. The guide includes clear cable trip hazards, but active handling and access context must be adjudicated.
- Human label review warranted: Yes: assess route obstruction and handling context; compare 016/017.

### 12. case_015 ? electrical_hazard

- Ground truth: `['working_at_height']`; prediction: `['electrical_hazard', 'working_at_height']`.
- Model description: The workers are in direct proximity to multiple large conductors and insulator-like components. The image does not establish whether the conductors are energized, isolated, or grounded, so the electrical condition remains uncertain.
- Model visual evidence: Multiple heavy parallel conductors run immediately beside and beneath the workers. | Insulator-like components and conductor connection hardware are visible around the work position. | The workers' hands and bodies are close to the conductor-support assembly. | No visible detail confirms de-energization, grounding, or insulation status.
- Human notes: Two workers are visibly performing work at a significant elevation on an overhead line structure. Hard hats and fall-protection equipment appear to be present. The image clearly supports a work-at-height condition, while no specific scaffold defect, unprotected edge, missing PPE, or unsafe electrical condition can be confidently established from the visible evidence.
- Assessment: **Clear model error relative to labeling rule**. Conductors and insulators plus unknown isolation/grounding are used as a positive electrical class. Lack of proof of de-energization does not prove a visible unsafe condition.
- Human label review warranted: Review class/review scope, not automatic positive relabeling; compare 017.

### 13. case_017 ? electrical_hazard

- Ground truth: `['housekeeping']`; prediction: `['electrical_hazard', 'housekeeping', 'missing_ppe']`.
- Model description: Illuminated bulbs and loosely routed electrical cords appear suspended over a visibly wet walking area. The electrical condition and protection cannot be confirmed from the image.
- Model visual evidence: Multiple illuminated bulbs are hanging directly from cords without visible protective guards. | Bundles of cables and loose cord loops are routed across the overhead frame. | Standing water and wet surfaces are visible on the floor beneath the electrical equipment.
- Human notes: The passageway is visibly cluttered with containers, equipment and uneven debris, and the floor appears wet or muddy in places. These conditions create a clear housekeeping and trip/slip hazard along the walking route. No specific electrical, fall-from-height, scaffolding or PPE hazard can be confidently established from the image.
- Assessment: **Potentially inconsistent ground truth**. Unlike ordinary cables, model evidence cites lit temporary lamps over wet flooring. The guide allows wet/unsafe electrical equipment; the image must establish an unsafe interaction or defect, not mere coexistence.
- Human label review warranted: Yes: inspect moisture exposure, connection protection and equipment condition; positive truth remains unproven.

### 14. case_017 ? missing_ppe

- Ground truth: `['housekeeping']`; prediction: `['electrical_hazard', 'housekeeping', 'missing_ppe']`.
- Model description: The person appears to be wearing open-toed sandals in an area with wet, uneven flooring and overhead materials. Protective headgear is not visible, although site-specific PPE requirements cannot be determined from the image alone.
- Model visual evidence: The person's feet are visible in open-toed sandals rather than enclosed protective footwear. | The person's head is clearly visible and no hard hat or other protective headgear is visible. | Overhead cables, fabric and structural members are visible above the walking route.
- Human notes: The passageway is visibly cluttered with containers, equipment and uneven debris, and the floor appears wet or muddy in places. These conditions create a clear housekeeping and trip/slip hazard along the walking route. No specific electrical, fall-from-height, scaffolding or PPE hazard can be confidently established from the image.
- Assessment: **Ambiguous visual evidence**. Sandals and uncovered head are concrete model claims; required footwear/headwear and work-zone context are unresolved. Combining footwear and helmet concerns obscures their different evidential strength.
- Human label review warranted: Yes: adjudicate each PPE item and contextual requirement separately.

### 15. case_020 ? missing_ppe

- Ground truth: `['working_at_height']`; prediction: `['missing_ppe', 'working_at_height']`.
- Model description: The worker is positioned at a miter saw, but safety glasses or a face shield and hearing protection are not visible. The image does not establish whether the saw is operating.
- Model visual evidence: The worker is leaning over a miter saw with hands near the saw table and workpiece. | The worker's face and ears are visible, but safety glasses, a face shield, earmuffs, or earplugs are not visible. | An orange hard hat is visibly worn.
- Human notes: A worker is visibly performing construction work at an elevated building level while using a powered cutting tool. A hard hat and what appears to be fall-protection equipment are visible, but the image does not clearly establish the complete edge-protection arrangement or whether the fall-arrest system is properly connected. The scene therefore supports a work-at-height condition and warrants human review.
- Assessment: **Potentially inconsistent ground truth**. Human notes describe use of a powered cutting tool but omit eye/hearing PPE; model describes a saw and no visible eye/ear protection but cannot establish operation. This is stronger task context than 001/013, yet activity and visibility remain unresolved.
- Human label review warranted: Yes: adjudicate active-tool status and PPE visibility; absence of visible earplugs alone is insufficient.

## False negative and label consistency

**case_007 / missing_ppe** is the sole false negative. The reviewer labels an absent high-visibility garment but explicitly says its requirement is unknown. The model omits missing_ppe and describes visible protective items. Under the written guide, an unknown task-dependent requirement does not justify a positive hazard. This annotation conflicts with safe case_006 (no vest, unknown requirement) and the conservative treatment in 001/008/013. Keep the scored FN in the original benchmark; adjudicate separately and version any future correction.

| Rule | Consistency finding | Adjudication scope |
| --- | --- | --- |
| Missing PPE | Requirement evidence applied unevenly; uncertainty itself sometimes creates a human positive. Possible omissions in 004/020 and unresolved footwear in 017. | Priority 007; also 004/017/020. Use 001/003/006/008/013/014 as comparison examples. |
| Working at height | Guide says elevation with fall exposure, but does not define whether controls eliminate the label. 003 excludes guarded exposure; 009/011/012 include it; 015/019 are positive with unresolved attachments. | 003 versus 009/011/012/015/019/020. Define exposure/activity versus uncontrolled condition before judging. |
| Unsafe scaffolding | Only one positive (010). Human notes cite narrow platform and incomplete visible protection but also uncertainty. Need a specific visible defect, not inability to confirm the whole scaffold. | 010; distinguish from 009/011/012/019. No FP was scored for this class. |
| Electrical hazard | 015 offers equipment/unknown energization only; 017 offers wet environment and temporary lights, potentially within the guide but not necessarily a proven defect. | 017 first; 015 as negative boundary. No positive ground-truth examples exist. |
| Housekeeping | Boundary between work materials/working lines and obstructed access is not consistently operationalized. | 004/007/011/014 against positives 016/017. |
| Review expectation | 019 explicitly says attachment cannot be established but expected review is false; comparable 009/011/012/020 expect true. 015 warrants the same review-scope check. | 015/019 and clear hazards 014/016/017; 018 for generic image limitation versus actionable uncertainty. |

## Human-review logic and actual triggers

The production decision is an OR of: raw model requires_human_review; raw ambiguity_detected; any hazard; overall confidence <0.85; number of sanity notes increases; or any substring uncertain/ambiguous/unclear/occluded/insufficient in the joined notes. RiskEngine scores are not terms in this expression. Hazard confidence <0.85 acts indirectly through sanity notes. Confidence is observation confidence, not hazard validity; high confidence does not prove a PPE requirement.
Rows below are the nine cases with expected_human_review=false and final=true. Flags overlap and must not be summed as independent causes. Due to Python short-circuit evaluation, the model flag is the first true OR term for eight rows; case_016 reaches the any-hazard term. Other true terms are independently sufficient, not necessarily executed at runtime.

| Case | Overall | Raw model | Ambiguity | Any hazard | Overall <.85 | Sanity added | Keyword | Hazard <.85 |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| case_001 | 0.92 | Yes | Yes | Yes | No | Yes | Yes | No |
| case_002 | 0.76 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| case_013 | 0.78 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| case_014 | 0.94 | Yes | Yes | Yes | No | Yes | Yes | No |
| case_015 | 0.9 | Yes | Yes | Yes | No | Yes | Yes | Yes |
| case_016 | 0.98 | No | No | Yes | No | No | No | No |
| case_017 | 0.93 | Yes | Yes | Yes | No | Yes | Yes | No |
| case_018 | 0.88 | Yes | Yes | No | No | Yes | Yes | No |
| case_019 | 0.94 | Yes | Yes | Yes | No | Yes | Yes | No |

Overlapping counts out of 9: {'model': 8, 'ambiguity': 8, 'any_hazard': 8, 'sanity': 8, 'keyword': 8, 'overall_low': 2, 'hazard_low': 3}. No affected case has overall or individual hazard confidence below 0.60; none lacks all visual-evidence items. Thus no <0.60 or empty-evidence trigger applies. Unknown requirements and occlusion still explain several model ambiguity flags.
Raw-model review alone flags 8/12 expected-negative cases; the provider increases this to 9/12 (case_016). That one-case difference is an offline descriptive counterfactual, not a recommendation to remove safety checks. All eight expected-review cases remain flagged in the stored final output.

### Review trace: case_001

Raw reasoning notes: The foreground is clear, while most site conditions in the background are blurred and cannot be reliably assessed. | Whether eye protection is mandatory for the visible activity cannot be determined from the image alone. | The male worker is not wearing a high-visibility vest, but the image does not establish that one is required for his role or location. | No visible elevation, open edge, scaffold access, exposed wiring, or clearly obstructed walking surface supports additional hazard categories. | This image-only review does not establish that the site is otherwise safe.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required.

### Review trace: case_002

Raw reasoning notes: Several projecting and bent rebar ends are visibly uncapped near the workers; this possible contact or impalement concern falls outside the six permitted hazard categories and should be reviewed on site. | The image does not clearly establish an elevated work position, an open edge, scaffolding, or an electrical hazard. | Facial occlusion prevents confirming whether eye protection is absent.
Added deterministic notes: Overall visual confidence below 0.85. Human review required. | The model reports ambiguous visual evidence. Human review required. | Eye protection not visible during rebar work: Uncertain visual evidence (confidence below 0.85). Human review required. | Eye protection not visible during rebar work: Evidence must name the PPE item and explain what appears absent/not visible. Human review required.

### Review trace: case_013

Raw reasoning notes: The material and purpose of the red tubing are not visually confirmed. | No exposed electrical conductor or energized component is visible, so an electrical hazard is not established. | The worker's lower body and surrounding floor are cropped, preventing assessment of footing, elevation, and nearby housekeeping conditions. | Whether gloves are mandatory for this specific task requires task and site-context review.
Added deterministic notes: Overall visual confidence below 0.85. Human review required. | The model reports ambiguous visual evidence. Human review required. | Possible missing hand protection: Uncertain visual evidence (confidence below 0.85). Human review required.

### Review trace: case_014

Raw reasoning notes: The worker's eyewear is visible, but the image does not establish whether it is rated eye protection. | The excavation has exposed soil faces, but stability, depth, protective systems, and access arrangements cannot be determined from this single view; excavation safety requires human review. | No working-at-height, scaffold, or electrical hazard is visually established. | Zero additional findings would not establish that the site is safe or replace a formal inspection.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required.

### Review trace: case_015

Raw reasoning notes: The substantial elevation is clear, but the exact height cannot be measured from the image. | Harness or belt components are visible; complete fall-arrest configuration and anchorage are partly obscured. | The conductor system's energized, isolated, or grounded status cannot be determined visually. | The lower worker is partly occluded by the striped structure and surrounding hardware.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required. | Elevated work on narrow utility-line structure: Height context is not described in the evidence. Human review required. | Possible proximity to electrical conductors: Uncertain visual evidence (confidence below 0.85). Human review required.

### Review trace: case_016

Raw reasoning notes: The image is a close-up of the floor; whether the lines are energized and their full routing are not visible. | No exposed conductors or other definite electrical defects are visible, so no separate electrical hazard is reported.
Added deterministic notes: none.

### Review trace: case_017

Raw reasoning notes: The image clearly supports wet-floor, obstruction and overhead electrical concerns. | The integrity, grounding and moisture protection of the electrical system are not visually verifiable. | The person's employment role and the site's specific PPE requirements cannot be confirmed from the image. | No visible elevation, open edge, ladder or identifiable scaffold supports a working-at-height, unprotected-edge or unsafe-scaffolding finding.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required.

### Review trace: case_018

Raw reasoning notes: The far end of the passage is blurred and partially obscured, so conditions there cannot be assessed reliably. | No clearly identifiable nearby workers are visible; PPE compliance cannot be evaluated for the indistinct distant figures. | The image alone cannot verify scaffold assembly, anchorage, load capacity, or overhead-work controls. | Zero detected hazards does not establish that the site is safe or replace a formal inspection.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required.

### Review trace: case_019

Raw reasoning notes: The image clearly shows elevation and scaffold climbing, but it does not show the full scaffold or anchorage system. | Harness attachment status is visually ambiguous because ropes, straps, and connectors overlap the scaffold. | The worker's hood obscures the head, so helmet use cannot be determined.
Added deterministic notes: The model reports ambiguous visual evidence. Human review required.

Two lexical sanity-check artifacts are confirmed by code and exact strings: case_002 says ?No safety glasses or goggles are visible?, but the absence-phrase list does not match that wording; it therefore adds a missing PPE-evidence note despite the item being named and its visibility described. case_015 says workers are ?above a distant cityscape?, but those tokens are absent from HEIGHT_TERMS, so the checker incorrectly says height context is not described. Neither artifact is the sole source of its review flag: both cases already have raw model review/ambiguity and predicted hazards.
The keyword detector also has no negation or relevance handling and includes sanity-generated notes. Its eight hits are highly correlated with added ambiguity notes, not eight separate discoveries. case_018 has zero hazards and confidence 0.88 but gets model ambiguity for blurred distant areas and inability to verify scaffold assembly; compare zero-review 005/006/008, which also describe image limitations. A missing global safety guarantee is not necessarily actionable ambiguity under the human negative-label policy.

## Dataset and interpretation limits

- Only 20 convenience images, seven safe scenes, 15 total positive class assignments, eight expected-review cases.
- One primary reviewer; AI-assisted annotation discussion; no secondary adjudication. The guide requests independent human evidence, so actual annotation provenance must be disclosed rather than claiming the guide proves independence.
- Class supports: missing_ppe 3, working_at_height 8, unprotected_edge 1, unsafe_scaffolding 1, electrical_hazard 0, housekeeping 2. Perfect results on one positive do not establish reliability.
- Zero electrical positives: recall is N/A. Electrical F1/precision penalties from two false positives cannot establish electrical detection ability.
- Four prior smoke-test photographs are reused. Prior model exposure and annotation discussion limit independence; do not call this independent validation.
- Audit classifications rely on frozen human notes and model evidence, not an independent expert image rereview. All suspect labels remain unchanged. The audit identifies adjudication questions, not corrected truth.
- The labeling guide contains stale setup wording (sixteen images still needed and no pilot integration) even though the run is complete; it remains untouched. Future protocol documentation should separate historical setup from current semantics.

## Prioritized improvement plan ? proposals only

| Priority / category | Problem addressed | Proposed mechanism | Effort | Trade-off |
| --- | --- | --- | --- | --- |
| P0 A: adjudicated label protocol | Unknown PPE requirement, height ontology and review-scope inconsistency | Define class evidence gates and uncertainty separately; have a second reviewer assess originals without predictions first, then reconcile 007 and comparator sets; version rather than overwrite original labels. | Medium: protocol plus human adjudication. | Reviewer time; changed label definitions affect comparability, so retain both versions. |
| P0 A: review-target definition | Clear hazards marked no-review while production mandates confirmation | Specify whether expected_human_review means perceptual uncertainty, operational confirmation or both; annotate separately in a future version. | Medium. | More annotation work; avoid retrofitting labels solely to improve the score. |
| P1 B: positive-hazard evidence gates | Cautioned prose still creates positive predictions | Require visible absence plus contextual PPE need; define obstruction/defect/exposure gates; put unsupported possibilities in limitations rather than hazard entries. Reconcile retain-low-confidence wording with supported-hazard threshold. | Low-medium prompt design; separate later validation required. | May suppress real but subtle hazards; keep uncertainty review available. No promised F1 gain. |
| P1 B: uncertainty scope and contrast examples | Generic incomplete scene coverage triggers ambiguity inconsistently | Define actionable uncertainty and pair supported-positive vs insufficient-evidence examples in a future prompt version using separate development images. | Medium. | Over-specific examples can overfit and under-escalate genuinely important unknowns. |
| P1 C: separate review reasons before changing flags | Any-hazard rule and model ambiguity conflate operational and uncertainty review | First specify distinct reason categories and evaluate them offline; only subsequently consider separate confirmation and uncertainty outputs under safety review. Preserve human confirmation requirements. | Medium-high due to workflow semantics; no implementation in this task. | Added complexity; removing blanket review without safeguards could reduce protection. |
| P2 C: semantic sanity checks and explicit reason evidence | Brittle phrase/token tests and correlated keyword flags | Cover paraphrases/negation and test the exact 002/015 cases; prefer explicit structured uncertainty reasons over arbitrary note words in a separately approved design. | Medium. | Semantic checks can themselves be brittle; avoid another paid inference layer or automatic threshold tuning. |
| P2 A: dataset extension and holdout | Low support and smoke reuse | Add independent site/session-separated photographs, electrical positives and harder negatives with blinded dual review. | High, primarily data/reviewer work. | Cost/time; new distribution makes old pilot figures non-comparable. |

No model, prompt, confidence threshold, RiskEngine, RAG or production behavior was changed. No expected F1 gain is claimed. First settle the label and review-target definitions; then evaluate a separately versioned proposal on held-out data under separate authorization.

## Verification

All 15 false-positive label assignments are covered exactly once above; the one false negative is retained. All 20 review flags were reproduced offline. Current manifest equals the frozen snapshot. SHA-256 checks confirm every existing run artifact, manifest, guide and backend Python source read for preservation remains unchanged. No regression suite or provider runner was launched because this task changes documentation only. Zero external API/model calls; zero paid calls.
