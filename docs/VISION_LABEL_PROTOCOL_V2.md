# Vision Label Protocol V2

Protocol ID: `vision-label-protocol-v2.0-proposed` · 2026-09-18
Status: proposed operational definitions for human approval and adjudication. This is not production `vision-v2`, a model prompt, or a revision to historical labels. Apply uniformly, including to cases where the choice may reduce scores. Do not use model agreement as an acceptance criterion.

## Common decision rule

Review the original photograph first. For each of the six classes record `positive`, `negative`, or `indeterminate`. Positive requires all class-specific evidence gates; negative means no supported instance in the visible scene, not certified site safety. Use indeterminate when a concrete relevant condition is visible but a missing detail could change the class decision. Generic inability to see the whole site is not alone a reason for indeterminate. Never convert indeterminate into a positive merely to request review, or into a negative to finish a dataset.

Record visible location/object, observation, inference, limiting factors and requirement source separately. Do not infer from filenames, prior labels or model outputs. Multiple classes can apply, but each requires distinct supporting evidence; one ambiguous fact must not automatically create several hazards.

An explicit site-specific PPE requirement may support a label only when supplied by a human as an authenticated, applicable requirement with source, date and task/zone scope. If supplied only to annotators, mark the case `context_required`: it must not be treated as a fair image-only prediction target. No requirements are supplied or invented by this preparation task. This protocol does not make legal compliance judgments.

Examples below are comparison references for the facilitator **after independent review**, not new answers. Reviewers initially receive this protocol with case references concealed; nobody should infer a revised label from an example. No existing case is relabeled here.

## 1. missing_ppe

- **Positive:** a specific PPE item is observably absent or not worn, and the observable task context or authenticated applicable site requirement establishes its need. Both gates must pass for that same item.
- **Required evidence:** adequate view of the relevant body area; named item and how absence is established; concrete task/exposure or requirement reference. Evaluate eye, head, hand, hearing and foot protection separately before combining the class.
- **Does not qualify:** obscured/cropped body part; inability to identify distant headwear; bare hands without demonstrated need for gloves; no high-visibility vest without relevant exposure/requirement; generic construction-site appearance as a blanket requirement for every item.
- **Ambiguity:** apparent tool use but operating state unknown; face in shadow; unseen earplugs; uncertain worker role or work-zone applicability.
- **Abstain/review:** indeterminate when the condition and missing fact are concretely relevant. If no supported task-specific requirement exists, do not assert missing_ppe. Qualified adjudication can resolve requirement applicability; unseen facts may remain unresolved.
- **Comparison references:** 007 versus 006/008/013 tests requirement consistency; 003/004/014 tests headwear and context; 020 tests powered-tool context. These are questions, not approved outcomes.

## 2. working_at_height

**Explicit choice: this class denotes visually supported elevated work activity/exposure, NOT proof of an uncontrolled fall hazard or defective protection.** A worker engaged in work, inspection, access or traversal on a visibly elevated construction platform/structure can qualify even when guardrails or a harness are present. This choice separates activity from protective-condition assessment and is fixed before human revision, not chosen by its effect on F1.

- **Positive:** a person performing work-related activity/access on an elevated surface or structure with credible physical elevation context.
- **Required evidence:** identifiable person and activity/location; visible relationship such as a raised platform, building-storey exterior, ladder/scaffold access, or a clear drop to a lower level. Record activity and protection observations separately.
- **Does not qualify:** scaffold/building in the background without a worker on it; camera perspective alone; an ordinary ground-level task; a harness alone; a person merely viewed against a skyline with no credible support/elevation relationship.
- **Ambiguity:** hidden footing, unknown depth, telephoto perspective, unclear presence/activity. No arbitrary height in metres is inferred.
- **Abstain/review:** uncertain elevation or activity is indeterminate. Known elevated activity can be positive while protection condition is unknown. Unknown attachment does not automatically create missing_ppe, unprotected_edge or unsafe_scaffolding.
- **Comparison references:** compare 003 with 009/011/012 and 015/019/020 using the same activity definition.
- **Limitation:** the label name remains historical, but the v2 activity definition is not equivalent to a legal fall-hazard finding. Revised-label scores cannot be directly presented as improvement over v1; no RiskEngine or workflow change follows from this proposal.

## 3. unprotected_edge

- **Positive:** a visible elevated edge/opening with credible fall potential and observably absent or inadequate protection along the exposed portion.
- **Required evidence:** location of edge/opening, lower-level/depth cues, visible protection gap/defect, and accessible exposure context. A worker need not be present if the exposed route is evident.
- **Does not qualify:** a dark recess of unknown depth; cropped rail assumed absent; a ground-level boundary; elevated work alone; inability to establish compliance dimensions.
- **Ambiguity:** hidden drop, unseen railing continuation, parapet dimension uncertainty, limited view of access.
- **Abstain/review:** indeterminate when fall potential or protection cannot be established. Do not use absence outside the frame as evidence.
- **Comparison references:** 004 and 007; distinguish known elevation from unknown recess depth. 003 provides a protected-boundary comparison without prescribing its label.

## 4. unsafe_scaffolding

- **Positive:** an identifiable scaffold has a specific visibly unsafe condition: a demonstrably incomplete supporting platform, visible damaged/disconnected support, clear instability, hazardous access, or a clearly missing protective component at an exposed working position.
- **Required evidence:** identify scaffold, exact defect, affected working/access position and visible consequence. Do not invent assembly or engineering requirements from a photograph.
- **Does not qualify:** scaffold presence, worker at height, hidden ties/anchors, narrow-looking perspective alone, inability to inspect the whole structure, or inability to see a harness attachment.
- **Ambiguity:** platform versus access member unclear; cropped components; temporary assembly stage without clear working use; scaffold versus another suspended-access system uncertain.
- **Abstain/review:** qualified human interpretation for a plausible defect; indeterminate if the specific component or required configuration remains unresolved.
- **Comparison references:** 010 versus 009/011/012/019. Confirm a specific defect instead of carrying forward the previous positive automatically.

## 5. electrical_hazard

- **Positive:** an observable unsafe electrical condition: visibly exposed conductor/damaged insulation, clearly unsafe connection, visibly hazardous contact/moisture exposure, or another specific shock/fire-risk condition supported by the image.
- **Required evidence:** electrical component, concrete defect/unsafe interaction and relevant exposure. Any claim about energization must have observable or authenticated evidence; unknown grounding/isolation does not prove a hazard.
- **Does not qualify:** intact visible cables, conductors/insulators alone, proximity to equipment alone, missing proof of de-energization, or water elsewhere in the same frame without a supported unsafe relationship.
- **Ambiguity:** wet surroundings but unknown equipment exposure/protection; uncertain cable damage or electrical identity; unknown live state needed for the conclusion.
- **Abstain/review:** request qualified adjudication where a concrete interaction is plausible; leave unresolved when required facts cannot be seen. Do not direct a reviewer to test live equipment for this image exercise.
- **Comparison references:** 015 versus 017; compare ordinary cable context in 013/016. The original set has zero electrical positives and offers no validated positive exemplar.

## 6. housekeeping

- **Positive:** visible obstruction of access, clear trip/slip hazard, dangerous debris accumulation, or comparably clear unsafe storage condition affecting a work/access surface.
- **Required evidence:** specific object/material/surface condition and its relationship to an accessible route, footing, occupied work area or clearly unstable storage. State the mechanism rather than simply saying clutter.
- **Does not qualify:** ordinary stored materials, required suspension/working lines, active work debris without clear unsafe interference, construction roughness alone, or an unsupported falling-object possibility mapped into housekeeping.
- **Ambiguity:** floor hidden behind materials; route unclear; necessary working lines versus loose obstruction; active handling versus unattended storage; uncertain wet/slippery surface.
- **Abstain/review:** indeterminate if route/exposure/mechanism cannot be established; obtain human assessment without assuming every coil is a trip hazard.
- **Comparison references:** 004/007/011/014 versus 016/017. Apply the same route/mechanism standard across these cases.

## Separate review concepts and proposed evaluation schema

**A. Perceptual uncertainty:** evidence cannot confidently establish a particular class or protection fact. Record which fact and why; clear elevated activity and uncertain attachment can coexist.

**B. Human safety adjudication:** a qualified person must interpret a concrete safety ambiguity, requirement applicability or disputed observation. Not every photographic limitation warrants it, and adjudication may conclude that evidence is insufficient rather than produce a binary answer.

**C. Operational confirmation:** a safety officer confirms a detected incident in the business workflow. A clear, high-confidence finding may still require it with no perceptual uncertainty. Dataset adjudication does not confirm, create or close a product incident.

Proposed evaluation-only schema (not implemented in production and not accepted by the existing legacy validator):

```json
{
  "schema_version": "vision-adjudication-v2-proposed",
  "protocol_version": "vision-label-protocol-v2.0-proposed",
  "case_id": "case_NNN",
  "image_hash": "original SHA-256",
  "source_dataset_version": "vision-pilot-20-v1-frozen",
  "class_decisions": {
    "missing_ppe": null,
    "working_at_height": null,
    "unprotected_edge": null,
    "unsafe_scaffolding": null,
    "electrical_hazard": null,
    "housekeeping": null
  },
  "class_evidence": [],
  "perceptual_uncertainty": null,
  "uncertain_facts": [],
  "requires_safety_adjudication": null,
  "adjudication_reason": null,
  "operational_confirmation": null,
  "context_required": null,
  "context_sources": [],
  "reviewer": null,
  "prior_exposure": null,
  "independent_review_completed_at": null,
  "secondary_reviewer": null,
  "adjudication_status": "pending",
  "rationale": null
}
```

Class values after human review: positive/negative/indeterminate. Null means unanswered, not negative. `class_evidence` entries name class, visible observation, inference, missing fact and requirement source. `operational_confirmation` is required/not_required/not_applicable under an explicitly documented workflow policy; null means unset. None of these new fields is populated automatically from the old ambiguous/expected_human_review flags or model output.

A future scorer must declare how indeterminate class targets are excluded or scored, report eligible denominators and coverage, and keep uncertainty/adjudication/confirmation metrics separate. Never silently map indeterminate to an empty hazard list. Confirmed positives may be derived only from human-completed class decisions in a separately versioned dataset. Do not apply this proposed schema retroactively to historical metrics.
