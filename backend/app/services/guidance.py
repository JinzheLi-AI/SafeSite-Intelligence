from app.models.entities import RegulationCitation

# Deliberately not represented as legislation, a retrieved source, or a verified standard.
DEMO_DOCUMENTS = [
    {'id': 'demo-fall', 'document_title': 'Demo field guide · Work at height', 'section': 'Sample checklist A',
     'jurisdiction': 'Demonstration / no legal jurisdiction', 'document_type': 'Sample field guide',
     'excerpt': 'Sample recommendation: isolate exposed work areas and have a competent person verify suitable fall protection.',
     'source_reference': 'demo://safesite/fall-prevention', 'verified': False, 'is_demo': True, 'status': 'DEMO / UNVERIFIED'},
    {'id': 'demo-edge', 'document_title': 'Demo field guide · Edge protection', 'section': 'Sample checklist B',
     'jurisdiction': 'Demonstration / no legal jurisdiction', 'document_type': 'Sample checklist',
     'excerpt': 'Sample recommendation: restrict access until incomplete edge protection has been inspected and restored.',
     'source_reference': 'demo://safesite/edge-protection', 'verified': False, 'is_demo': True, 'status': 'DEMO / UNVERIFIED'},
    {'id': 'demo-general', 'document_title': 'Demo site induction · General safety', 'section': 'Sample checklist C',
     'jurisdiction': 'Demonstration / no legal jurisdiction', 'document_type': 'Sample induction',
     'excerpt': 'Sample recommendation: document observations and escalate unresolved hazards to the site safety officer.',
     'source_reference': 'demo://safesite/site-induction', 'verified': False, 'is_demo': True, 'status': 'DEMO / UNVERIFIED'},
]


def demo_citation(hazard_id: int, hazard_type: str) -> RegulationCitation | None:
    # No match means no citation. A real retrieval adapter must return grounded evidence.
    index = {'working_at_height': 0, 'unprotected_edge': 1}.get(hazard_type)
    if index is None:
        return None
    doc = DEMO_DOCUMENTS[index]
    return RegulationCitation(hazard_id=hazard_id, **{k: doc[k] for k in (
        'document_title', 'section', 'jurisdiction', 'excerpt', 'source_reference', 'verified', 'is_demo')})
