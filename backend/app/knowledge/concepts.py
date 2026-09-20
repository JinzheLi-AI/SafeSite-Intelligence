import re
CONCEPTS = {
    'working_at_height': ['work at height', 'fall from height', 'fall protection', 'fall arrest', 'working platform', 'safety harness'],
    'unprotected_edge': ['open edge', 'floor edge', 'guardrail', 'guard-rail', 'edge protection', 'fencing', 'opening', 'toe-board'],
    'missing_ppe': ['helmet', 'personal protective equipment', 'ppe', 'safety shoes', 'goggles', 'gloves', 'protective clothing'],
    'unsafe_scaffolding': ['scaffold', 'scaffolding', 'bamboo', 'metal scaffold', 'working platform', 'bracing', 'putlog'],
    'electrical_hazard': ['electrical', 'electricity', 'electric shock', 'power cord', 'earthing', 'electric equipment'],
    'housekeeping': ['housekeeping', 'passage', 'access', 'obstruction', 'trip', 'tidy', 'clean', 'rubbish', 'waste'],
}
STOP = set('a an the of and or to for in on at with without visible appears worker workers construction site safety please find guide guidance source requirement requirements'.split())
def tokens(text: str) -> set[str]:
    synonyms = {'passage':'access','route':'access','tidy':'housekeeping','cleanliness':'housekeeping',
                'clean':'housekeeping','guardrail':'edge','guard':'edge','obstruction':'blocked',
                'obstructed':'blocked','electric':'electrical','electricity':'electrical','helmet':'helmet'}
    return {synonyms.get(w.rstrip('s'), w.rstrip('s')) for w in re.findall(r'[a-z]{3,}',text.lower()) if w not in STOP}
def categories(text: str, allowed: list[str]) -> list[str]:
    low = text.lower()
    return [str(h) for h in allowed if any(term in low for term in CONCEPTS[str(h)])]
