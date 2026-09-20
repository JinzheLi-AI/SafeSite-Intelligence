# OpenAI Sol vision pilot: vision_openai_sol_20_20260918_01

20-image pilot dataset; single primary reviewer; AI-assisted annotation discussion; no secondary adjudication. These results are neither independent validation nor production-level accuracy. Electrical-hazard class has zero positive support.

- Dataset SHA-256: `14157204b8b9bd7941046563e9e162be25845e4ef0536608b311a6884635c116`
- Requested model: gpt-5.6-sol. Actual returned models: gpt-5.6-sol.
- Production prompt: vision-v1; unchanged. No benchmark-specific prompting, retries, mock fallback or DeepSeek.
- Status: completed. Successful: 20/20; failed: 0; unattempted: 0; coverage: 100.00%.
- Checkpoint case_001 was saved before remaining cases ran sequentially. Recorded attempts are never automatically repeated, including interrupted attempts with unknown outcomes.
- Previous failed benchmark lock/reports and historical smoke evidence were preserved.

## Metrics on successful predictions only

| Metric | Result |
| --- | ---: |
| Micro precision | 48.28% |
| Micro recall | 93.33% |
| Micro F1 | 63.64% |
| Macro F1 | 57.35% |
| Exact label-set match | 45.00% |
| Multi-hazard exact match | 50.00% |
| Safe-scene false-positive rate | 42.86% |
| Expected-human-review recall | 100.00% |
| Unnecessary-review rate | 75.00% |

Classification uses raw model hazard categories, deduplicated into sets, not RiskEngine scores. Human-review flags are production outputs after guardrails, separate from classification. Undefined denominators are null/N/A. Macro F1 excludes undefined class F1 values; defined class count: 6. A zero-support class cannot establish recall or class coverage even if false positives yield a defined F1.

| Class | TP | FP | FN | Evaluated support | Dataset support | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| missing_ppe | 2 | 7 | 1 | 3 | 3 | 22.22% | 66.67% | 33.33% |
| working_at_height | 8 | 1 | 0 | 8 | 8 | 88.89% | 100.00% | 94.12% |
| unprotected_edge | 1 | 1 | 0 | 1 | 1 | 50.00% | 100.00% | 66.67% |
| unsafe_scaffolding | 1 | 0 | 0 | 1 | 1 | 100.00% | 100.00% | 100.00% |
| electrical_hazard | 0 | 2 | 0 | 0 | 0 | 0.00% | Unavailable | 0.00% |
| housekeeping | 2 | 4 | 0 | 2 | 2 | 33.33% | 100.00% | 50.00% |

Safe scenes evaluated: 7; correctly predicted empty: 4; false-positive scenes: 3. Safe-scene false categories: ['missing_ppe'].
Expected-review cases evaluated: 8; true flags: 8; missed flags: 0.

## Usage and latency

Input tokens: 76572; output tokens: 14215; total tokens: 90787. Missing usage is never treated as zero.
Latency: mean 14387.65 ms; median 14892.0 ms; p95 nearest rank 23214 ms.
Estimated cost: unavailable (no reliable configured estimate).

## Main findings

There are 15 false-positive class assignments and one false negative. PPE contributes seven false positives; housekeeping four; electrical two; height and edge one each. Safe-scene PPE false positives are cases 001, 002 and 013. The sole false negative is missing_ppe in case_007, whose human note also describes uncertainty about the PPE requirement. These are disagreements with frozen labels, not independently adjudicated errors. No prompt or labels were changed.

Electrical recall is N/A: there are no positive electrical examples. Electrical precision/F1 of zero penalize two false positives only and do not establish detection ability. Macro F1 uses all six defined F1 values, including this penalty.

## Case-level errors

All disagreements are retained below and in case_errors.json. Explanations compare frozen human notes with model claims; they do not amend annotations.

### case_001

Ground truth: []; prediction: ['missing_ppe'].
False positives: ['missing_ppe']; false negatives: [].
Likely error category (interpretive): PPE requirement inferred without task evidence
Explanation: Model flags eyewear while explicitly acknowledging that the task requirement is unknown; frozen label is safe.
Human notes: Two workers are visibly wearing hard hats, and one worker is also wearing a high-visibility vest. No exposed edge, unsafe scaffolding condition, electrical hazard, obstructed access route, or other supported hazard can be confidently identified from the visible scene.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["Both workers' eyes are visibly uncovered.", "Clear safety glasses are hanging from the male worker's clothing rather than being worn.", "The workers are positioned in a construction-site setting, but the immediate activity appears to involve a clipboard and handheld device."], "description": "Neither worker appears to be wearing eye protection. The image does not establish whether their current task or location requires it."}]

### case_002

Ground truth: []; prediction: ['missing_ppe'].
False positives: ['missing_ppe']; false negatives: [].
Likely error category (interpretive): not-visible vs missing confusion; occluded PPE
Explanation: Model flags eyewear while describing shaded/partly obscured faces and acknowledging absence cannot be confirmed.
Human notes: Two workers are wearing hard hats and high-visibility vests while working around reinforcement steel. No exposed edge, fall-from-height condition, unsafe scaffold, electrical hazard, or obstructed access route can be confidently identified from the visible scene.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["Both foreground workers are visibly wearing yellow hard hats, high-visibility vests, and work gloves.", "No safety glasses or goggles are visible on the portions of either worker's face shown.", "The left worker's face is shaded and partly obscured by the hard-hat brim; the right worker is looking downward."], "description": "Safety glasses or other eye protection are not visible on the two foreground workers while they appear to be handling reinforcing steel. The workers' downward-facing positions and helmet brims partially obscure their faces, so absence cannot be confirmed from this image alone."}]

### case_003

Ground truth: ['missing_ppe']; prediction: ['missing_ppe', 'working_at_height'].
False positives: ['working_at_height']; false negatives: [].
Likely error category (interpretive): working-at-height over-detection
Explanation: Model includes height exposure despite describing a multi-rail barrier; reviewer did not label immediate fall exposure.
Human notes: Two workers are standing in an elevated construction-area environment while holding hard hats rather than wearing them. Their heads are clearly visible and uncovered. A guardrail is present along the edge, so the image does not clearly support an unprotected-edge hazard. The scene is elevated, but the visible guardrail reduces the evidence for an immediate fall-exposure condition.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["The center-left worker has an uncovered head and is holding a yellow hard hat.", "The worker on the right has an uncovered head and is carrying a yellow hard hat against the torso.", "Safety glasses are visibly hanging from the right worker's hand.", "Both foreground workers are wearing high-visibility vests and work gloves."], "description": "The two foreground workers appear to have uncovered heads while holding hard hats. The worker on the right also holds safety glasses below waist level rather than wearing them."}, {"hazard_type": "working_at_height", "evidence": ["A distant cityscape and buildings far below are visible beyond the workers, indicating an elevated location.", "Both foreground workers are positioned immediately beside a horizontal metal perimeter railing.", "Multiple horizontal rail members are visible along the open side."], "description": "The workers are standing beside a visibly elevated perimeter overlooking terrain and buildings below. A multi-rail metal barrier is present, but the image does not establish its dimensions, condition, or compliance."}]

### case_004

Ground truth: ['working_at_height', 'unprotected_edge']; prediction: ['housekeeping', 'missing_ppe', 'unprotected_edge', 'working_at_height'].
False positives: ['housekeeping', 'missing_ppe']; false negatives: [].
Likely error category (interpretive): housekeeping subjectivity; PPE annotation disagreement
Explanation: Model claims an uncovered head and displacement risk from stored materials. Human notes focus on fall exposure. This may include annotation omission or a differing threshold; no independent adjudication establishes which interpretation is correct.
Human notes: Workers are positioned at an elevated building opening close to the exterior edge. The visible edge protection appears limited to a low concrete upstand rather than a complete guardrail system. The scene supports possible fall exposure, although the exact working height and complete protection arrangement cannot be fully confirmed from this image.
Model visual evidence: [{"hazard_type": "unprotected_edge", "evidence": ["A seated worker is positioned directly beside the low concrete boundary at the front of the opening.", "Three standing workers are gathered within a short distance of the same boundary.", "Only a low concrete upstand is visible along the front; no full-height top rail and midrail are visible."], "description": "Several workers are immediately beside an exterior opening. The visible concrete boundary appears low, and no full-height guardrail system is visible across the occupied area."}, {"hazard_type": "working_at_height", "evidence": ["The occupied floor opening is visibly above the exterior foreground and utility lines.", "One worker is seated with feet and body close to the slab boundary.", "No personal fall-arrest attachment is visible on the workers, although equipment may be concealed by clothing or the viewing angle."], "description": "Workers appear to be occupying an elevated slab or opening, including one person seated close to its outer boundary. The exact elevation and fall-protection arrangements cannot be confirmed from the image."}, {"hazard_type": "missing_ppe", "evidence": ["The standing worker near the center has visible hair and no hard hat on the head.", "The worker is wearing a high-visibility vest and is positioned among scaffolding and stored masonry materials.", "Three nearby workers are visibly wearing hard hats."], "description": "One worker inside the construction area has a clearly visible uncovered head while nearby workers are wearing hard hats."}, {"hazard_type": "housekeeping", "evidence": ["Multiple stacks of loose bricks are positioned near the front opening.", "Long boxed or board-like materials are leaning beside the low concrete boundary on the right.", "The stored materials are adjacent to an occupied work and access area."], "description": "Bricks and long boxed or board-like materials are stored near the low exterior boundary, creating a possible displacement or falling-object concern."}]

### case_007

Ground truth: ['missing_ppe']; prediction: ['housekeeping', 'unprotected_edge'].
False positives: ['housekeeping', 'unprotected_edge']; false negatives: ['missing_ppe'].
Likely error category (interpretive): edge-depth ambiguity; housekeeping subjectivity; PPE annotation disagreement
Explanation: Model labels a possible opening of unknown depth and local debris, but omits the human-labeled uncertain high-visibility PPE concern. The human notes themselves acknowledge the PPE requirement is unknown. This is the sole scored false negative, not proof that the human interpretation is definitive.
Human notes: The worker is wearing a hard hat, face covering and gloves, but no high-visibility vest is visible. The image does not establish whether a high-visibility garment is required for this specific task or work zone, so the PPE finding should be treated as uncertain and subject to human review.
Model visual evidence: [{"hazard_type": "housekeeping", "evidence": ["A loop of reinforcing steel projects upward from the concrete directly in front of the worker.", "Loose concrete fragments and uneven broken surfaces are visible around the worker's hands and knees.", "A dark cable lies across the foreground work surface."], "description": "The immediate work surface contains a raised loop of reinforcing steel, loose concrete debris, and a cable, creating possible contact or trip hazards."}, {"hazard_type": "unprotected_edge", "evidence": ["A concrete edge borders a dark recessed area at the lower-right side of the image.", "No cover or guard is visible over the portion of the possible opening shown in the frame.", "The worker is positioned near the visible edge, although the exact distance is unclear."], "description": "A dark recess bordered by concrete is visible at the lower right and may be an uncovered slab opening. The image does not show enough of the area to establish its depth or fall potential."}]

### case_011

Ground truth: ['working_at_height']; prediction: ['housekeeping', 'missing_ppe', 'working_at_height'].
False positives: ['housekeeping', 'missing_ppe']; false negatives: [].
Likely error category (interpretive): image resolution/distance limitation; not-visible vs missing confusion; housekeeping subjectivity
Explanation: Model flags uncertain helmet identification and platform lines, while human notes label height exposure only.
Human notes: Workers are visibly operating on a suspended exterior work platform at significant elevation. The platform has visible guardrails, but the image does not clearly show the workers’ fall-arrest attachment or the full condition of the suspension system. The scene clearly supports work-at-height exposure and warrants human review of the protection arrangements.
Model visual evidence: [{"hazard_type": "working_at_height", "evidence": ["The platform is visibly suspended against an upper-story building façade by multiple vertical lines.", "The worker is standing on the platform beside an open window or façade recess.", "Yellow harness-like straps are visible across the worker's back and legs.", "No fall-arrest attachment or connection point is clearly visible in the image."], "description": "The worker is operating on a suspended platform several stories above ground. A harness appears visible, but its connection to an independent lifeline or anchor is not visible."}, {"hazard_type": "housekeeping", "evidence": ["A large coil of dark cable hangs near the center of the platform.", "Multiple cables or hoses run along and across the platform guardrail area.", "Several loose rope ends and loops hang from the right side and center of the platform."], "description": "Coiled cables and several loose lines are draped over or attached around the platform framing, presenting possible snagging, entanglement, or trip concerns."}, {"hazard_type": "missing_ppe", "evidence": ["The worker's head is visible, but the dark covering does not have clearly distinguishable hard-hat features.", "Image distance and shadows obscure the exact type of headwear."], "description": "A clearly identifiable safety helmet is not visible on the worker; dark headwear or image distance makes this observation uncertain."}]

### case_013

Ground truth: []; prediction: ['missing_ppe'].
False positives: ['missing_ppe']; false negatives: [].
Likely error category (interpretive): PPE requirement inferred without task evidence
Explanation: Model flags bare hands while explicitly acknowledging that the need for gloves cannot be determined.
Human notes: The worker is visibly wearing a hard hat and safety glasses. The visible red cable or hose does not by itself establish an electrical hazard, and no fall, edge, scaffolding, or housekeeping hazard can be confidently identified from the scene.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["The worker's left hand is visibly gripping red tubing or conduit without a glove.", "The worker's right hand is also visibly bare against the masonry surface.", "A yellow hard hat and clear safety glasses are visibly worn."], "description": "The worker appears to be manipulating tubing or conduit with bare hands. Gloves are not visible, although the task-specific need for gloves cannot be determined from the image alone."}]

### case_014

Ground truth: ['missing_ppe']; prediction: ['housekeeping', 'missing_ppe'].
False positives: ['housekeeping']; false negatives: [].
Likely error category (interpretive): housekeeping subjectivity
Explanation: Model interprets cable/coil placement and uneven excavation ground as a trip concern; reviewer labels only missing head protection.
Human notes: The worker is standing in an active construction/excavation area with his head fully visible and no hard hat being worn. No clear evidence supports a working-at-height, unprotected-edge, scaffolding, electrical, or housekeeping hazard in this image.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["A soft gray knit cap is visible on the worker's head.", "No hard hat is visible on or immediately beside the worker.", "The worker is surrounded by excavated soil, rocks, and an exposed soil face."], "description": "The worker appears to be wearing a soft knit cap rather than protective headwear while inside an active excavation area."}, {"hazard_type": "housekeeping", "evidence": ["A cable or hose extends across the ground directly in front of and beside the worker's boots.", "The worker is holding a large coil with loops hanging near knee and foot level.", "The walking surface is visibly uneven and contains loose rocks and soil."], "description": "A long cable or hose and a large coil are positioned at the worker's feet on rough, debris-covered ground, creating a possible trip or entanglement hazard."}]

### case_015

Ground truth: ['working_at_height']; prediction: ['electrical_hazard', 'working_at_height'].
False positives: ['electrical_hazard']; false negatives: [].
Likely error category (interpretive): electrical-object vs electrical-hazard confusion
Explanation: Model labels proximity to conductors while acknowledging energization, isolation and grounding cannot be established.
Human notes: Two workers are visibly performing work at a significant elevation on an overhead line structure. Hard hats and fall-protection equipment appear to be present. The image clearly supports a work-at-height condition, while no specific scaffold defect, unprotected edge, missing PPE, or unsafe electrical condition can be confidently established from the visible evidence.
Model visual evidence: [{"hazard_type": "working_at_height", "evidence": ["Two workers are positioned above a distant cityscape on a narrow metal assembly.", "The upper worker has one foot supported on a small structural member while working beside the striped assembly.", "The lower worker is leaning outward from the structure with a belt or harness visible around the waist.", "Ropes, straps, and metal connection hardware are visible, but individual fall-arrest attachment points cannot be confirmed."], "description": "Both workers appear to be working at substantial elevation while supported by narrow metal framing and cable-related components. Belts or harness components are visible, but the image does not clearly show whether each worker has continuous fall-arrest attachment to a suitable anchor."}, {"hazard_type": "electrical_hazard", "evidence": ["Multiple heavy parallel conductors run immediately beside and beneath the workers.", "Insulator-like components and conductor connection hardware are visible around the work position.", "The workers' hands and bodies are close to the conductor-support assembly.", "No visible detail confirms de-energization, grounding, or insulation status."], "description": "The workers are in direct proximity to multiple large conductors and insulator-like components. The image does not establish whether the conductors are energized, isolated, or grounded, so the electrical condition remains uncertain."}]

### case_017

Ground truth: ['housekeeping']; prediction: ['electrical_hazard', 'housekeeping', 'missing_ppe'].
False positives: ['electrical_hazard', 'missing_ppe']; false negatives: [].
Likely error category (interpretive): electrical-object vs electrical-hazard confusion; PPE annotation disagreement
Explanation: Model cites lighting/cords above wet ground plus sandals and headwear. Reviewer labels only housekeeping. Electrical protection and task-specific PPE requirements remain unresolved in the model explanation.
Human notes: The passageway is visibly cluttered with containers, equipment and uneven debris, and the floor appears wet or muddy in places. These conditions create a clear housekeeping and trip/slip hazard along the walking route. No specific electrical, fall-from-height, scaffolding or PPE hazard can be confidently established from the image.
Model visual evidence: [{"hazard_type": "electrical_hazard", "evidence": ["Multiple illuminated bulbs are hanging directly from cords without visible protective guards.", "Bundles of cables and loose cord loops are routed across the overhead frame.", "Standing water and wet surfaces are visible on the floor beneath the electrical equipment."], "description": "Illuminated bulbs and loosely routed electrical cords appear suspended over a visibly wet walking area. The electrical condition and protection cannot be confirmed from the image."}, {"hazard_type": "housekeeping", "evidence": ["The person is walking on a visibly wet floor with pooled water.", "A hose crosses the walking route near the person's feet.", "The floor contains uneven channels, raised edges and broken or irregular surfaces.", "Containers, machinery and miscellaneous materials narrow the available passage.", "A loose rag or fabric item is lying on the floor in the foreground."], "description": "The narrow route contains standing water, irregular floor surfaces, a hose and other obstructions that present possible slip and trip hazards."}, {"hazard_type": "missing_ppe", "evidence": ["The person's feet are visible in open-toed sandals rather than enclosed protective footwear.", "The person's head is clearly visible and no hard hat or other protective headgear is visible.", "Overhead cables, fabric and structural members are visible above the walking route."], "description": "The person appears to be wearing open-toed sandals in an area with wet, uneven flooring and overhead materials. Protective headgear is not visible, although site-specific PPE requirements cannot be determined from the image alone."}]

### case_020

Ground truth: ['working_at_height']; prediction: ['missing_ppe', 'working_at_height'].
False positives: ['missing_ppe']; false negatives: [].
Likely error category (interpretive): not-visible vs missing confusion; PPE requirement uncertainty
Explanation: Model flags eye/hearing protection near a saw but cannot establish whether it is operating; reviewer labels height exposure only.
Human notes: A worker is visibly performing construction work at an elevated building level while using a powered cutting tool. A hard hat and what appears to be fall-protection equipment are visible, but the image does not clearly establish the complete edge-protection arrangement or whether the fall-arrest system is properly connected. The scene therefore supports a work-at-height condition and warrants human review.
Model visual evidence: [{"hazard_type": "missing_ppe", "evidence": ["The worker is leaning over a miter saw with hands near the saw table and workpiece.", "The worker's face and ears are visible, but safety glasses, a face shield, earmuffs, or earplugs are not visible.", "An orange hard hat is visibly worn."], "description": "The worker is positioned at a miter saw, but safety glasses or a face shield and hearing protection are not visible. The image does not establish whether the saw is operating."}, {"hazard_type": "working_at_height", "evidence": ["The worker is visible above a foreground wall or parapet, indicating an elevated work position relative to the camera.", "A harness and coiled rope or lanyard are visible around the worker's torso and waist.", "No attached lifeline or connection to an anchor point is visible within the image.", "The foreground wall obscures the worker's footing and the nearby edge."], "description": "The worker appears positioned on an elevated level and is wearing a harness, but no connection from the harness to an anchor is visible. The foreground wall obscures the platform and edge conditions, so fall exposure cannot be confirmed."}]

## Reproduction and limits

Evaluation regression suite: 80 passed, two existing dependency warnings. Reports are regenerated from the raw cache and interpretive error notes; no inference is used.
From safesite: `backend/.venv/Scripts/python.exe -m evaluation.report_resumed_pilot --run-id vision_openai_sol_20_20260918_01`. This regenerates reports offline without inference.
raw_results.json contains the frozen annotations, original/processed image hashes, normalized successful results, usage and request provenance. The byte lock prevents concurrent writers. Resume requires the same dataset/prompt hashes and skips all recorded attempts. A stopped run requires investigation; no automatic restart is allowed.
Small convenience sample, possible annotation subjectivity and AI-assisted discussion limit generalization. No secondary adjudication and no positive electrical examples. Prior smoke exposure means these images are not a fresh independent held-out set. Confidence averages are descriptive, not formal calibration.
Manifest, images, .env and prompt unchanged: True.
