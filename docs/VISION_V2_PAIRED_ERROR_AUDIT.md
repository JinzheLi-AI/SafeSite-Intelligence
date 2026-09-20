# Offline audit: paired Vision V1/V2 development errors

## Scope and evidence

Audit of evaluation/reports/paired_live_20260919_step16/state.json, both metrics files, manifest_snapshot and current development manifest, production prompts.py/vision_v2.py, real.py normalization, vision_contracts.py, VISION_LABEL_PROTOCOL_V2.md and the actual local photographs. All ten photos inspected in a contact sheet; 003/005/010 additionally inspected at full stored resolution. Sources are the cached brief evidence/notes, not hidden model reasoning. No external calls, prompt edits, label edits, scoring changes or V2.1 implementation.

The dataset has 10 development images; 20 genuine calls completed previously. V1 TP/FP/FN=7/10/0; V2=5/7/2. Net FP reduction is three but hides six removed and three newly introduced FPs. This single paired sample does not establish prompt causality or stable model behavior: stochastic variation is uncontrolled.

Offline checks: all 20 raw hazard lists exactly match normalized prediction categories; all 10 V2 uncertainty-review flags reproduce through the existing deterministic function. Thus no category was removed or added by normalization. RiskEngine changes scores, not classification membership. No metrics recomputed under new definitions.

## Electrical false negative: 003

Human rationale identifies the improvised temporary light's multiple connections lacking complete protective enclosure; it explicitly does NOT establish moisture contact. The actual photo shows the lit bulb, hanging cable/connection components and a separate dark floor patch. Fine connection protection cannot be conclusively certified from this image alone. A bare bulb or cables alone would not establish the label.

V1 cites loose suspended electrical components and incomplete enclosure/mechanical protection, also mentioning possible wetness. V2 acknowledges an illuminated lamp and associated wiring but says: "insufficient evidence of direct moisture contact with electrical components, exposed conductors, or visible electrical damage"; it explicitly requests closer electrical inspection and omits the category. It instead labels the floor patch housekeeping with 0.97 confidence, escalating V1's "possibly wet" into a definite puddle.

Confirmed mechanism: explicit model abstention under its evidence interpretation, not normalization loss. Plausible prompt contribution: V2 lists "visible damage, exposed conductors or unsafe moisture contact" as examples but does not explicitly exemplify inadequate guarding of identifiable connection assemblies. The model appears to have treated examples as the decisive checklist and failed to address the annotation's enclosure mechanism. We cannot prove it visually recognized the exact unguarded connection defect, or that wording alone caused this. V2 accepted uncovered connection access on 002 without a bare conductor, so this is inconsistent application, not a universal bare-copper rule.

Qualified review should confirm the component/accessible-contact defect on 003 without relying on the wet patch. Do not automatically erase the human label or count V1's success as proof of every assertion in its evidence.

## Scaffold false negative: 005

The photo visibly has discontinuities, loose/hanging sections and large openings in facade mesh. The central projecting fan-shaped assembly may be intentionally designed. These are different candidate conditions and must not be conflated.

The human annotation explicitly targets damaged external protective mesh, not structural instability. V1 describes both bowed geometry and torn/folded/detached screening, giving 0.78 confidence. V2 recognizes irregular projecting mesh geometry but says it may be "intentional catch-fan construction or damage" and explicitly makes no unsafe_scaffolding finding. It does not separately assess the tears/loose facade screening in its notes. Lack of mention does not prove the damage was not perceived.

Confirmed mechanism: model abstention about fan geometry plus failure to cover the annotated protective-system defect in its stated assessment. There is NO evidence V2 explicitly demanded structural instability: neither its prompt nor cached explanation requires that. The prompt's generic "specific visible defect and affected work/access location" can leave protective mesh scope underspecified. The protocol includes missing protective components at exposed work positions but does not explicitly define torn containment netting or distinguish purpose-made gaps. This is a real category-boundary clarification need, not grounds for automatic relabeling. A qualified reviewer should confirm protective function, defect and affected area; do not infer that every tear-looking opening is a safety defect.

## Three height false positives are not one cause

| Case | Image / raw evidence | Finding |
|---|---|---|
| 005 | Unfinished high-rise levels/netting; raw evidence explicitly says no workers visible | Clear infrastructure-to-activity inference. V2 calls available elevated platforms credible construction access without an observed person. |
| 008 | Scaffold platforms/rails/toe boards/ladders; raw evidence explicitly says no personnel visible | Clear scaffold-presence-to-activity inference, despite otherwise correctly declining a scaffold defect and unclear housekeeping. |
| 010 | A worker reaches over a partition on a landing visibly above several steps | NOT a no-worker hallucination. Raw description correctly separates raised activity from uncontrolled fall hazard. Negative ground truth may conflict with the broad protocol. |

Exact V2 wording: "identify credible elevated work activity or access, including guarded platforms." It does not repeat the protocol's explicit requirement for an identifiable person and activity/location, nor its exclusion of a scaffold/building without a worker. This omission plausibly permits the 005/008 interpretations; categories already occur in raw output, so normalization is not the origin. Do not fix them by requiring absent guardrails: guarded elevated work intentionally remains in scope.

For 010, the protocol permits a person doing work/access on a visibly elevated surface, with a raised platform or clear lower level, and sets no arbitrary metre threshold. The image and V2 evidence plausibly satisfy that definition. The existing note establishes housekeeping but does not justify a height-negative exception for raised entrance landings. Request targeted definition/adjudication: ordinary stair/landing access versus in-scope elevated work. Do not blindly teach V2.1 that stairs never count, and do not change this scored FP retrospectively.

## Electrical improvements to retain

004: V1 labels an open wet cabinet-like object electrical although it explicitly cannot identify electrical components. V2 withholds electrical because unsafe electrical contact cannot be established. It also withholds housekeeping because access/work-path obstruction is unclear.

006: V1 infers possible mechanical damage from unguarded cables on paving despite no visible damage and no established traffic route. V2 correctly avoids turning intact equipment, an unseen lead termination, or unknown grounding into a positive.

007: V1 extrapolates electrical danger from a portable unit on folded sheeting and hidden cable routing. V2 separates visible trip obstructions (retained housekeeping) from intact electrical equipment (no visible damage/contact). This category separation should be preserved.

Keep all existing prohibitions against electrical equipment alone, hypothetical cable damage, unknown isolation/grounding, water elsewhere in frame, and unseen cable segments as positives. Add a narrowly evidenced connection-guarding example rather than weakening the entire electrical gate.

## Other case differences and unresolved annotation questions

001 still receives housekeeping from both models despite negative truth: inferred use of trench footing versus unclear actual access/exposure. V2 removes unsupported unprotected_edge. 002 keeps electrical positive in both; V2 separates uncertainty about insulation/energization from the observable open compartment. 009 keeps height/edge positives plus PPE and housekeeping scored FPs. V2 improves PPE rationale by dropping the hard-hat assumption and identifying open footwear near reinforcement/debris, but stored missing_ppe remains negative. The existing annotation only explains unknown hard-hat requirement; it does not address the footwear exposure argument. That and the visible ladder/debris route merit targeted human consistency review, not automatic acceptance of the model. No PPE positives exist in this dataset, so this run cannot validate PPE recall.

Ground-truth issues requiring specific review: 010 elevated-activity scope is the strongest apparent protocol mismatch; 005 protective netting scope and 003 connection guarding require qualified boundary assessment; 009 footwear/task requirement and housekeeping route rationale are incomplete relative to model claims. Cases 001/003 housekeeping remain exposure/route judgments, not proven model errors solely because they are scored FPs. Case 008's approved indeterminate housekeeping label stays masked and unchanged.

## Uncertainty review: exact trigger audit

V2 expected positives are 001/008. Actual positives are 001?006. Therefore TP=001; FP=002/003/004/005/006; FN=008; TN=007/009/010. Recall=1/2; unnecessary-review rate=5/8. These are discrepancies against stored expectations, not proof that every extra review is clinically/operationally unnecessary.

All six actual positives already have raw requires_human_review=true AND ambiguity_detected=true. Four (002/004/005/006) ALSO have overall confidence <0.85; 002 additionally has hazard confidence <0.85. None is caused solely by deterministic thresholds. None is caused by missing visual_evidence. Deterministic rules amplify/redundantly enforce model uncertainty; they do not independently introduce any FP here. Operational confirmation is computed separately from any hazard, and does not cause these uncertainty flags.

- 002 FP: model explicitly cannot establish insulation integrity/energization and gives 0.82 confidence. Stored safety-adjudication=true but uncertainty=false. This mixes a real localized visual uncertainty with qualified interpretation; adjudicate the distinction rather than assume it is just operational review.
- 003 FP: explicit uncertainty about exposed components/moisture and electrical status; human expects qualified adjudication but not visual uncertainty. The missed electrical mechanism and review expectation are linked. A flag for the unresolved electrical judgment is not caused by the housekeeping operational confirmation.
- 004 FP: open cabinet identity and damp interior are ambiguous; model turns missing evidence for a positive into actionable review (0.82), while annotation regards no identifiable electrical hazard as sufficient. Define an actionable unresolved question versus generic inability to inspect interiors.
- 005 FP: genuine uncertainty about fan design versus damage, with confidence 0.82; safety-adjudication=true in truth. Focus the review on protective mesh function/defect rather than geometry alone.
- 006 FP: unresolved yellow-green lead termination leads to uncertainty/0.78. No exposed conductor established. This resembles a normal photographic limitation promoted to review; qualified judgment may still be justified if a specific suspect connection is identifiable.
- 008 FN: model explicitly says route location of ground conduit is unclear, but both raw flags=false and overall confidence=0.96 (height hazard=0.98). Existing function uses structured flags/confidence/evidence presence, not free-text keyword scans; it faithfully returns false. This is semantic inconsistency in model output, not a parser loss. Confidence in an incorrect height observation masks an unrelated housekeeping uncertainty.

Schema observation: one overall confidence and generic reasoning_notes cannot identify which class-specific unknown fact merits review. V2's raw requires_human_review has been redefined as uncertainty, but the prompt simultaneously says generic limitations are not actionable and concrete unresolved visual questions require flags. 004/006 over-flag while 008 under-flags similar missing-context prose. Any claim that keyword matching or removing thresholds alone fixes this is unsupported.

## Minimal V2.1 proposal ? NOT implemented

| Proposal | Mechanism / effort | Trade-off / regression obligation |
|---|---|---|
| Electrical: explicitly assess identifiable accessible connection assemblies with visibly inadequate guarding/enclosure; name component, defect and exposure. State examples are non-exhaustive. | Addresses 003 checklist narrowing; small prompt-only candidate after qualified definition review. | Do not classify bare bulbs, intact cords, an unidentified open box, or remote wetness alone. Retain 004/006/007 negatives and 002 positive counterexamples in new development tests. |
| Scaffold: explicitly separate load-bearing defects, work/access protection and protective mesh/containment defects; assess each visible component independently of uncertain catch-fan geometry. | Addresses 005 attention/category scope; small wording change after boundary adjudication. | No automatic positive for planned openings, installation stage, designed fans, or non-safety screening. Require visible consequence/location, not proven overall structural instability. |
| Height: require an identifiable person visibly performing work/access on an elevated support; idle platforms/buildings/netting/ladders alone are insufficient. | Direct 005/008 correction; small prompt clarification matching existing protocol. | Retain guarded work positives; resolve 010 landing boundary before encoding a new exception. No invented height threshold. |
| Review: first clarify annotation expectations; then request a specific unresolved fact, affected class and decision consequence, distinguish generic unseen internals from actionable uncertainty. | Prompt-only first; separate later optional typed class-specific uncertainty contract and consistency check (medium effort). | Preserve operational confirmation and current numeric thresholds initially. Do not implement brittle phrase scanning or auto-set review for every omitted category. Typed changes require backward compatibility and separate evaluation. |

Keep category and review proposals separate for attribution. Do not force predictions to match these ten labels. No F1 improvement estimate is justified.

## Regression tests and independent evaluation

Future offline fixtures should cover: positively identified unguarded connections without moisture; intact equipment/cables with unknown grounding; water separate from wiring; protective-mesh defects versus planned openings/fans; empty scaffold/building/stairs; visible guarded elevated worker; raised landing boundary after adjudication; clear trip obstruction versus uncertain route; actionable unknown with all hazards omitted; confident unrelated hazard plus another class's uncertainty; qualified interpretation separate from operational confirmation. Test raw/normalized category parity, preserved thresholds, explicit review provenance, legacy V1 flags unavailable, and indeterminate masking. Mock tests check contracts/logic, NOT visual accuracy.

Any V2.1 changes based on this audit are development-set tuning. Keep these ten images and related source/site groups out of future held-out data. Acquire NEW licensed held-out scenes, cover all classes (including PPE positives and close electrical/scaffold negatives), use consistent protocol and preferably independent secondary adjudication, freeze labels/prompts/preprocessing/scoring before inference, and compare prompts on identical held-out images under a new explicit paid-call authorization. Do not inspect held-out results and then describe post-tuning reuse as independent validation.

## Complete cached case-level evidence ledger

The ledger below records every predicted category and its visual evidence for both versions, alongside the actual human decisions. It preserves distinctions that aggregate metrics conceal. Quotations are local cached output, not new inference.

### v2_development_001

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "negative"}`

Human evidence: Yellow protective conduits and black cables are visible in an excavated area. No exposed conductors, visibly damaged insulation, or other specific electrical hazards can be confidently identified. The cable connections and installation status are not fully visible, so some uncertainty remains. No other clear hazards are identified in the image.

**vision-v1** ? categories: housekeeping, unprotected_edge; overall confidence 0.88; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- unprotected_edge (0.9): The excavation has abrupt, uneven sides and no barrier or edge protection is visible within the photographed area. Evidence: A deep open excavation occupies most of the image. | Abrupt soil and broken-concrete edges are visible along both sides. | No guardrail, barricade, cover, or warning barrier is visible in the image.

- housekeeping (0.88): Loose branches, roots, broken soil or concrete, and short corrugated conduit sections are scattered around the excavation, creating possible obstruction or footing concerns if personnel enter it. Evidence: Several short yellow corrugated conduit sections lie loose on the right side of the excavation. | Branches, roots, vegetation, and broken soil or concrete are scattered across the trench area. | Loose material occupies space beside and over the installed black conduits or cables.

Notes: The image is tightly cropped, so barriers or access controls outside the frame cannot be assessed. | Excavation depth and whether personnel must enter the area cannot be determined precisely from the image. | Black and yellow service components are visible, but their contents and energized status cannot be determined; no electrical hazard is asserted. | No workers are visible, so PPE and worker exposure cannot be evaluated. | Zero visibility of trench support does not establish that support is absent; soil conditions and excavation stability require on-site review.

**vision-v2** ? categories: housekeeping; overall confidence 0.87; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation True.

- housekeeping (0.9): Branches, roots, rubble, and loose duct sections occupy portions of the narrow trench floor around the installed conduits, creating an obstruction for anyone accessing the work area. Evidence: Several loose yellow corrugated duct sections lie across the right side of the trench floor. | Branches, roots, and broken soil or rubble are scattered through the narrow area beside the installed black conduits. | The loose material occupies potential footing space within the utility installation area.

Notes: The excavation is visibly open, but its depth cannot be reliably determined from the image. | The trench perimeter is cropped, so the presence or adequacy of edge protection cannot be assessed. | The visible black lines and yellow ducts show no exposed conductors, visible damage, or unsafe moisture contact.

### v2_development_002

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "positive", "housekeeping": "negative"}`

Human evidence: The lamppost has an open electrical access compartment with visible wiring and connections. Several connections appear to be wrapped with tape or improvised insulating materials, leaving the installation insufficiently protected from the surrounding environment. These visible conditions support an electrical hazard. Whether the wiring is energized and the exact electrical condition require on-site verification. No other supported hazards are identified.

**vision-v1** ? categories: electrical_hazard; overall confidence 0.96; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- electrical_hazard (0.96): Electrical cables and multiple taped or sleeved connections are visible inside an uncovered, weather-exposed cavity, creating a possible contact or moisture-related electrical hazard. Evidence: A rectangular cavity in the concrete pole is visibly open with no cover plate. | Several insulated wires and connection points are accessible within the opening. | Multiple connections appear wrapped with red, black, or transparent material. | Vegetation and weathering are visible around and inside the cavity.

Notes: The image clearly shows an uncovered cavity containing wiring, but it does not establish whether the circuit is energized. | The condition of conductors beneath the tape or sleeves cannot be confirmed visually. | The dark surroundings prevent assessment of access controls or nearby people.

**vision-v2** ? categories: electrical_hazard; overall confidence 0.82; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation True.

- electrical_hazard (0.82): Electrical wiring and multiple taped connection assemblies are exposed within an uncovered recess. The open compartment permits direct access and environmental exposure; the integrity of the irregular wrapping is uncertain. Evidence: A rectangular recess in the concrete pole is visibly open with no cover in place. | Multiple insulated wires and taped connection assemblies are visible inside the recess. | Some connection wrapping appears irregular and loosely layered, with debris or vegetation present around the wiring.

Notes: The image does not establish whether the wiring is energized. | No clearly bare conductor is distinguishable; transparent or irregular wrapping makes insulation integrity uncertain. | The pole's surrounding access conditions and height of the recess are not shown.

### v2_development_003

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "positive", "housekeeping": "negative"}`

Human evidence: An illuminated bare light bulb is suspended from an improvised wiring arrangement in an unfinished room. Multiple electrical connections and cables are visible without a complete protective enclosure. These conditions support an electrical hazard involving inadequate protection of the temporary lighting installation. A small wet patch is also visible on the floor, but contact with the wiring cannot be established. The exact electrical condition requires on-site verification. No other hazard category is confidently established.

**vision-v1** ? categories: electrical_hazard, housekeeping; overall confidence 0.91; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- electrical_hazard (0.93): The illuminated temporary light is surrounded by loosely hanging wiring and electrical components that do not appear fully enclosed or mechanically protected. A possible wet patch is visible on the floor below the installation. Evidence: A bare illuminated bulb is hanging from wiring near the center-left of the image. | Multiple wires and small electrical components are loosely suspended around the vertical service pipes. | A long cable is loosely routed across the concrete wall without visible conduit or continuous mechanical protection. | A dark patch that appears possibly wet is present on the floor directly below the temporary installation.

- housekeeping (0.87): A possible wet patch and loosely hanging service wiring/components may create localized slipping or snagging hazards. Evidence: A dark irregular patch that appears possibly wet is visible on the concrete floor. | Several wires and components hang loosely around the central service installation. | A stool or small work platform and a leaning red-handled item partially occupy the right side of the floor area.

Notes: No workers are visible, so PPE use cannot be assessed. | The light is visibly illuminated, but the image does not establish the condition of hidden connections or protective devices. | The dark floor patch appears possibly wet, but its substance and source cannot be confirmed visually. | A qualified on-site inspection is needed to determine whether the electrical components are adequately insulated, enclosed, grounded, and protected.

**vision-v2** ? categories: housekeeping; overall confidence 0.91; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation True.

- housekeeping (0.97): A localized puddle creates a slip hazard in the floor area beside the service risers. Evidence: A dark liquid puddle is visible on the concrete floor at the base of the vertical service risers. | The puddle occupies an otherwise open floor area where a person could stand or walk while accessing the services.

Notes: An illuminated temporary lamp and associated wiring are visible above the puddle. | The image provides insufficient evidence of direct moisture contact with electrical components, exposed conductors, or visible electrical damage; electrical hazard status requires closer inspection.

### v2_development_004

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "negative"}`

Human evidence: Three outdoor electrical cabinets or equipment enclosures are visible. Their doors appear closed, and no exposed conductors, visibly damaged insulation, or other specific unsafe electrical conditions can be identified. Fallen leaves are present on the ground but do not clearly obstruct a walking route. No supported hazard is identified in the image.

**vision-v1** ? categories: electrical_hazard, housekeeping; overall confidence 0.76; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- electrical_hazard (0.68): A cabinet-like enclosure appears to have an open front, leaving its dark interior exposed to outdoor conditions. No conductors or energized components are clearly visible, so the electrical nature and status require verification. Evidence: The center black enclosure has a visibly open front rather than a closed door or cover. | Moisture droplets are visible across the exposed interior surface. | No wiring, terminals, or other energized parts are clearly discernible inside the enclosure.

- housekeeping (0.82): Loose or projecting cables, supports, and metal frame members appear at ground level around the cabinets. Whether this area is used as a pedestrian route is not visible. Evidence: A black cable or hose runs across the ground between the orange and black enclosures. | Metal support legs and rectangular frame members project across leaf-covered ground around the equipment. | A short black cable or conduit projects outward near the base of the gray cabinet.

Notes: The image does not show workers, active construction operations, or a defined pedestrian route. | The center enclosure's interior is too dark to identify electrical components or confirm energized status. | The equipment's purpose and operating condition cannot be determined visually.

**vision-v2** ? categories: (empty); overall confidence 0.82; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation False.

Notes: The center enclosure has an apparently open front and visible moisture on its interior surface, but no conductors or identifiable electrical components are visible; unsafe electrical contact cannot be established. | Metal supports and cables or hoses are visible around the cabinet bases, but the image does not clearly establish that they obstruct a designated access or work path. | No workers are visible, so task-specific PPE requirements or PPE absence cannot be assessed.

### v2_development_005

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "positive", "electrical_hazard": "negative", "housekeeping": "negative"}`

Human evidence: The high-rise construction facade is covered by scaffold netting, with multiple visible tears, large openings, and loose or displaced sections of protective mesh. These are observable defects in the scaffold's external protective system and support an unsafe_scaffolding label. The image does not establish structural instability of the scaffold itself, and on-site inspection is required to determine the extent of the defect. No workers or other supported hazard categories are clearly identified.

**vision-v1** ? categories: unsafe_scaffolding; overall confidence 0.78; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- unsafe_scaffolding (0.78): The high-rise perimeter mesh and supporting framework appear irregular and locally deformed. This may indicate damaged or displaced scaffold screening or containment equipment, but the system's intended design is not visually verifiable. Evidence: A large mesh-panel assembly between the buildings is strongly bowed outward, with multiple support members converging toward one area. | Green perimeter sheeting is loose and hanging in several locations, with visible gaps exposing the building facade. | Sections of mesh along the left facade appear torn, folded, or detached from adjacent screening.

Notes: The image is taken from a distance, so connections, anchors, and structural condition cannot be confirmed. | The bowed assembly could be a purpose-designed configuration; onsite inspection is needed to distinguish intentional geometry from deformation. | No workers are clearly visible, so worker PPE and individual exposure cannot be assessed.

**vision-v2** ? categories: working_at_height; overall confidence 0.82; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation True.

- working_at_height (0.9): Numerous unfinished floor levels and exterior platform/protection systems are visibly positioned high above ground, indicating credible access for elevated construction work. This observation does not establish an uncontrolled fall hazard. Evidence: Multiple unfinished concrete floor levels are visible across the high-rise structures. | Exterior platforms, framing, and perimeter netting extend across many elevated storeys. | No workers are visible in the image.

Notes: The large outward-projecting mesh assembly near the center-right has irregular geometry, but the image does not establish whether this is intentional catch-fan construction or damage; no unsafe_scaffolding finding is made. | Perimeter details are partly obscured by netting and distance, so visibly absent or inadequate edge protection cannot be confirmed. | No workers are visible, so PPE absence cannot be assessed.

### v2_development_006

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "negative"}`

Human evidence: A temporary electrical distribution box with circuit breakers, industrial sockets, and connected power cables is visible. The protective covers appear intact, and no exposed conductors, visibly damaged insulation, or clearly defective electrical connections can be identified. Power cables extend onto the ground, but the image does not establish that they obstruct a pedestrian route. No supported hazard is identified.

**vision-v1** ? categories: electrical_hazard; overall confidence 0.78; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- electrical_hazard (0.78): Several connected power cables lie directly on the paved surface and appear to lack cable ramps or other mechanical protection. This could expose them to impact or abrasion if the area is used by vehicles, equipment, or pedestrians. Evidence: Two thick black cables exit the lower electrical connectors and run across the pavement in the foreground. | Another black cable lies across the pavement behind the distribution unit. | No cable ramps, guards, or raised routing are visible around these cables. | The distribution-board covers appear closed, and no exposed conductors are visible.

Notes: The image does not establish whether the paved area is an active pedestrian or vehicle route. | Cable condition, electrical energization, grounding, and protective-device operation cannot be verified visually. | The two white objects on the ground cannot be reliably identified from the image.

**vision-v2** ? categories: (empty); overall confidence 0.78; raw review/ambiguity True/True; normalized uncertainty True; operational confirmation False.

Notes: A thin yellow-green lead is visible beside the lower-left cable connector, but the image does not clearly show its termination or any exposed conductor; electrical safety cannot be determined from this view. | The heavy cables rest on the paved surface, but no defined pedestrian access route or clear obstruction is visible, so a housekeeping finding is not supported.

### v2_development_007

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "positive"}`

Human evidence: A temporary electrical distribution box is positioned on loose plastic sheeting beside a paved area. Power cables extend across the ground, and loose plastic sheeting and a wooden board are scattered around the equipment. These visible conditions create potential trip hazards and support a housekeeping hazard. The electrical sockets and connections do not show clearly exposed conductors, damaged insulation, or another specific electrical defect. No other supported hazard is identified.

**vision-v1** ? categories: electrical_hazard, housekeeping; overall confidence 0.9; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- housekeeping (0.96): Wrinkled plastic sheeting, a timber board, cables, and other loose materials occupy the paved area around the distribution unit, creating possible trip and access obstructions. Evidence: A large sheet of folded and wrinkled plastic covers much of the paved surface. | A timber board lies diagonally across the sheeting. | Electrical cables run through and alongside the loose materials.

- electrical_hazard (0.8): The connected distribution unit appears to rest partly on uneven, folded sheeting, which may affect stability and expose the cable to mechanical damage. The image does not establish the unit's electrical condition or environmental rating. Evidence: The yellow electrical distribution unit is visibly connected to a thick orange cable. | The unit's feet or lower edges appear positioned among folds of loose plastic sheeting. | The connected cable passes into the piled sheeting and is partly obscured.

Notes: The image clearly shows loose materials and a connected portable electrical unit. | The surface condition beneath the unit and the cable section hidden by sheeting cannot be fully assessed. | No workers are visible, so actual exposure frequency cannot be determined from the image alone. | The image does not allow verification of internal electrical protection, grounding, inspection status, or weather resistance.

**vision-v2** ? categories: housekeeping; overall confidence 0.96; raw review/ambiguity False/False; normalized uncertainty False; operational confirmation True.

- housekeeping (0.97): Loose sheeting, timber, and leads are spread across the paved surface around the equipment, creating clear snagging and trip points for anyone accessing the unit or passing through the area. Evidence: A large crumpled sheet covers much of the paved surface around and beneath the yellow power distribution unit. | A loose timber board lies diagonally across the sheet in front of the unit. | Electrical leads run across the paved surface and through the loose sheeting.

Notes: The power unit and connectors appear intact in the visible area; no exposed conductors, obvious cable damage, or unsafe moisture contact is visible. | No workers or elevated work areas are visible.

### v2_development_008

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "indeterminate"}`

Human evidence: A scaffolded multi-storey facade is visible with overhead cable-support structures and red-and-white cabinets behind temporary fencing. A flexible conduit loops on the gravel and grass beside the paved edge in the foreground. The photograph does not show the yellow portable distribution box on plastic sheeting described in the previous note. Whether the conduit obstructs a pedestrian route is not established by the image alone; the existing housekeeping judgment requires a case-specific supporting rationale.

**vision-v1** ? categories: housekeeping; overall confidence 0.91; raw review/ambiguity False/False; normalized uncertainty None; operational confirmation None.

- housekeeping (0.93): Coiled and trailing flexible conduit, small debris, and uneven gravel are present along the edge of the sidewalk and could create a trip or access obstruction if the area is entered. Evidence: A long flexible conduit is visibly coiled on the gravel and grass near the lower-right edge of the image. | Another length of conduit visibly runs parallel to the curb beside the paved sidewalk. | Loose stones and small construction debris are visible on the uneven ground around the conduit.

Notes: No workers are visible, so PPE use cannot be assessed. | The scaffold is visible from only one exterior viewpoint; connections, access arrangements, and full platform conditions cannot be verified from this image. | Closed equipment cabinets are visible, but no exposed electrical components or visibly damaged conductors are apparent.

**vision-v2** ? categories: working_at_height; overall confidence 0.96; raw review/ambiguity False/False; normalized uncertainty False; operational confirmation True.

- working_at_height (0.98): The building façade is served by multiple scaffold platforms at substantial elevations. This establishes credible access and work at height, although visible edge rails and toe boards indicate protection along many sections. Evidence: Multiple scaffold platforms are visibly installed at successive levels of the building façade. | Horizontal top rails and intermediate rails are visible along many platform edges. | Red toe boards are visible along numerous scaffold platform edges. | Access ladders are visible within the scaffold structure. | No personnel are visible on the scaffold in this image.

Notes: The image does not show a specific visibly defective scaffold component. | Building openings are viewed through the scaffold rails; the image does not clearly establish an unprotected floor edge. | Ground-level hoses or conduits are not clearly located in a designated pedestrian or work access route.

### v2_development_009

Ground truth: `{"missing_ppe": "negative", "working_at_height": "positive", "unprotected_edge": "positive", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "negative"}`

Human evidence: A person is standing on an elevated concrete slab with visibly unprotected edges and no apparent guardrails or other edge barriers. These conditions support working_at_height and unprotected_edge labels. Protruding reinforcement bars are also visible, but this risk is outside the current six hazard categories. Although the person is not wearing a hard hat, the applicable PPE requirements cannot be established from the image alone. No other supported hazard is identified.

**vision-v1** ? categories: housekeeping, missing_ppe, unprotected_edge, working_at_height; overall confidence 0.95; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- unprotected_edge (0.98): The elevated concrete slab has open perimeter sections without visible guardrails or another edge-protection system. Evidence: The slab perimeter is visibly open along the left and rear sides. | No top rail, midrail, or solid edge barrier is visible at these perimeter sections. | The structure and vegetation below the slab establish visible elevation at the left edge.

- working_at_height (0.91): The person is on an elevated slab near unprotected perimeter areas, and no fall-arrest attachment is visible. Evidence: The person is visibly positioned on an elevated concrete slab. | Open slab edges are visible within the same work area. | No harness, lanyard, lifeline, or attachment point is visible on the person.

- missing_ppe (0.96): The person appears to have no hard hat and is visibly wearing flip-flops rather than protective work footwear. Evidence: The person's uncovered hair and head are visible; no hard hat is visible. | The person appears to be wearing open, thin flip-flop-style footwear. | Protruding reinforcing bars and loose construction materials are present in the walking area.

- housekeeping (0.94): Uncapped protruding reinforcement and scattered materials are visible across the slab, creating possible trip, puncture, or impalement hazards. Evidence: Multiple vertical reinforcing bars protrude from the slab without visible protective caps. | A ladder-like wooden item lies flat across the slab near the lower center. | Loose soil, boards, metal pieces, and other materials are scattered across the walking surface. | A line or cable extends across part of the slab.

Notes: The image clearly shows elevation and open slab edges, but the exact fall distance cannot be measured from the image. | No fall-arrest equipment is visible; equipment outside the frame or concealed by clothing cannot be ruled out. | The function of the line crossing the slab is unclear, so it is not classified as an electrical hazard. | A single image cannot establish overall site compliance or safety.

**vision-v2** ? categories: housekeeping, missing_ppe, unprotected_edge, working_at_height; overall confidence 0.95; raw review/ambiguity False/False; normalized uncertainty False; operational confirmation True.

- working_at_height (0.96): A person is walking on an elevated concrete slab above a lower roof and surrounding vegetation. Evidence: The person is visibly standing and walking on the concrete slab. | A lower corrugated roof is visible beside and below the slab. | The slab perimeter is visible around the elevated work surface.

- unprotected_edge (0.97): Multiple slab perimeter sections have no visible guardrail or equivalent edge protection, creating fall exposure for the person on the slab. Evidence: The left and far slab edges are visibly open without guardrails. | The person is on the same slab surface as the unprotected perimeter. | A lower roof and vegetation are visible beyond and below portions of the slab edge.

- missing_ppe (0.93): The person is wearing open sandals while walking among protruding reinforcement and loose construction materials, leaving the feet visibly unprotected from puncture and impact hazards. Evidence: Open sandals and exposed portions of the person's feet are visible. | Multiple reinforcing bars protrude vertically from the slab. | Loose construction materials and debris are present on the walking surface.

- housekeeping (0.94): A ladder and scattered materials lie across the slab and may obstruct movement or create trip hazards. Evidence: A wooden ladder is lying flat across the slab rather than being stored upright or outside the walking area. | Loose boards, metal pieces, and debris are scattered on the slab. | The person is walking on the same surface where these obstructions are present.

Notes: The exact slab height is not measurable from the image, but elevation is visually established by the lower adjacent roof and surroundings. | No hard-hat finding is made because a specific overhead or falling-object exposure is not visibly established.

### v2_development_010

Ground truth: `{"missing_ppe": "negative", "working_at_height": "negative", "unprotected_edge": "negative", "unsafe_scaffolding": "negative", "electrical_hazard": "negative", "housekeeping": "positive"}`

Human evidence: Loose cables run diagonally across the construction access stairs and landing. Small pieces of debris and construction materials are also scattered on the steps. These visible obstructions create a clear trip hazard along the access route and support a housekeeping label. The worker is wearing a hard hat and high-visibility vest. No specific electrical defect or other supported hazard is clearly established.

**vision-v1** ? categories: housekeeping, unprotected_edge; overall confidence 0.9; raw review/ambiguity True/True; normalized uncertainty None; operational confirmation None.

- housekeeping (0.97): Loose lines, construction debris, and materials obstruct portions of the stairs and adjacent walking surfaces. Evidence: Several orange lines run diagonally across the lower work area and toward the elevated landing. | Loose rubble, a plastic bottle, a brick-like block, and other debris are visible on the stair treads. | A pipe, boards, and miscellaneous materials are lying across the lower-left walking surface.

- unprotected_edge (0.82): The elevated landing and adjacent lower work area appear to include open level changes without continuous guardrail protection. Evidence: A visible drop separates the elevated landing from the lower-left work surface. | The perimeter is only partially bordered by low unfinished masonry walls, with no continuous guardrail visible. | The worker is standing on the elevated landing near the partially enclosed perimeter.

Notes: Image perspective does not establish the exact height of the visible level changes; the edge concern requires on-site verification. | The worker's hard hat and high-visibility vest are visible; other PPE cannot be reliably assessed from this view. | The orange lines may be cords, cables, or similar temporary lines; their function and energized status are not visually determinable. | No damaged conductor or other direct evidence of an electrical hazard is visible. | This image does not replace a formal site inspection.

**vision-v2** ? categories: housekeeping, working_at_height; overall confidence 0.95; raw review/ambiguity False/False; normalized uncertainty False; operational confirmation True.

- working_at_height (0.93): The worker is performing a task on a landing elevated above the lower foreground level. Stairs provide access to the work position, and no uncontrolled fall condition is established from this view. Evidence: A worker is standing and reaching over a block partition on the upper entrance landing. | A flight of multiple steps visibly connects the landing to the lower foreground level.

- housekeeping (0.97): Several loose items occupy stair treads and could interfere with footing along the visible access route. Evidence: A masonry fragment lies near the center of a lower stair tread. | A plastic bottle and an orange cloth or bag are lying on upper stair treads. | Dust and small construction debris are scattered across the stairs.

Notes: The visible worker is wearing a hard hat and high-visibility vest; the image does not establish a requirement for additional PPE. | The image does not clearly establish an unprotected fall edge, a scaffold defect or an unsafe electrical condition.

## Preservation

Only this new audit document was written. All inspected dataset, image, prompt/provider and existing report file hashes were checked unchanged. Zero OpenAI/DeepSeek calls, zero paid inference, zero benchmark runs. Offline consistency assertions passed for 20 label-set comparisons and 10 deterministic review reconstructions; no product code was changed and no new regression suite was needed for this documentation-only audit.
