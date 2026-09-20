import re
from app.ai.vision_contracts import VisualInspectionOutput

HEIGHT_TERMS = {'elevated', 'elevation', 'edge', 'edges', 'scaffold', 'scaffolding', 'ladder', 'platform',
                'roof', 'rooftop', 'balcony', 'slab', 'storey', 'story', 'height'}
PPE_TERMS = {'helmet', 'hardhat', 'gloves', 'goggles', 'glasses', 'eyewear', 'mask', 'respirator',
             'vest', 'boots', 'footwear', 'harness', 'lanyard', 'earplugs', 'earmuffs'}
ABSENCE_PHRASES = ('not visible', 'no visible', 'absent', 'missing', 'without', 'uncovered',
                   'no helmet', 'no hard', 'no gloves', 'no goggles', 'no vest', 'not wearing')


def review_notes(output: VisualInspectionOutput) -> list[str]:
    """Lightweight evidence checks. These flag uncertainty; they do not prove safety."""
    notes = list(output.reasoning_notes)
    if output.overall_confidence < 0.60:
        notes.append('Insufficient or uncertain overall visual evidence (confidence below 0.60). Human review required.')
    elif output.overall_confidence < 0.85:
        notes.append('Overall visual confidence below 0.85. Human review required.')
    if output.ambiguity_detected:
        notes.append('The model reports ambiguous visual evidence. Human review required.')
    for hazard in output.hazards:
        prefix = hazard.title + ': '
        evidence = ' '.join(hazard.visual_evidence).casefold()
        words = set(re.findall(r"[a-z]+", evidence))
        if not hazard.visual_evidence:
            notes.append(prefix + 'No concrete visual evidence supplied; evidence is insufficient. Human review required.')
        if hazard.confidence < 0.60:
            notes.append(prefix + 'Insufficient/uncertain visual evidence (confidence below 0.60). Retained for human review.')
        elif hazard.confidence < 0.85:
            notes.append(prefix + 'Uncertain visual evidence (confidence below 0.85). Human review required.')
        if hazard.hazard_type == 'working_at_height' and not words.intersection(HEIGHT_TERMS):
            notes.append(prefix + 'Height context is not described in the evidence. Human review required.')
        if hazard.hazard_type == 'missing_ppe':
            item_named = bool(words.intersection(PPE_TERMS)) or 'hard hat' in evidence or 'high visibility' in evidence
            absence_described = any(phrase in evidence for phrase in ABSENCE_PHRASES)
            if not item_named or not absence_described:
                notes.append(prefix + 'Evidence must name the PPE item and explain what appears absent/not visible. Human review required.')
    return list(dict.fromkeys(notes))
