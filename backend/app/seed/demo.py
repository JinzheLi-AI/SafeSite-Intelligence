import argparse
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import Base, engine, SessionLocal, utcnow
from app.models.entities import Project, Site, Inspection, Hazard, Incident, CorrectiveAction, AuditLog
from app.ai.mock import MockSafetyAIProvider
from app.schemas.contracts import ConfirmFindings
from app.services.risk import RiskEngine
from app.services.workflow import analyze, audit
from app.models.documents import KnowledgeDocument
from app.services.guidance import DEMO_DOCUMENTS

HAZARDS = [
    ('working_at_height', 'Fall protection check at facade', 5, 4, 4),
    ('missing_ppe', 'Eye protection missing in cutting zone', 3, 3, 3),
    ('unprotected_edge', 'Incomplete temporary edge barrier', 5, 3, 4),
    ('unsafe_scaffolding', 'Scaffold access requires inspection', 4, 4, 4),
    ('electrical_hazard', 'Temporary cable exposed to damage', 4, 3, 3),
    ('housekeeping', 'Materials obstructing access route', 2, 2, 3),
]


def seed_database(db: Session):
    for document in DEMO_DOCUMENTS:
        if not db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.source_reference == document["source_reference"])):
            db.add(KnowledgeDocument(**{key: value for key, value in document.items() if key != "id"}))
    if db.scalar(select(Project).where(Project.code == 'HR-P2')):
        db.commit()
        return
    anchor = utcnow().replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=1)
    project = Project(name='Harbour Residence Phase 2', code='HR-P2', location='Harbour District · Demo Site', created_at=anchor - timedelta(days=60))
    db.add(project)
    db.flush()
    sites = [Site(project_id=project.id, name='Tower A', zone='East construction zone'),
             Site(project_id=project.id, name='Tower B', zone='West construction zone'),
             Site(project_id=project.id, name='Ground Works', zone='Logistics & access')]
    db.add_all(sites)
    db.flush()
    for index in range(18):
        kind, title, severity, exposure, probability = HAZARDS[index % 6]
        created = anchor - timedelta(days=19 - index)
        site = sites[index % 3]
        risk = RiskEngine.assess(kind, severity, exposure, probability, 0.89)
        inspection = Inspection(project_id=project.id, site_id=site.id, location_text=f'Level {3 + index} · Zone {index % 3 + 1}',
            source_type='DEMO', description='Deterministic historical demo record.', status='CONFIRMED',
            created_at=created, completed_at=created)
        db.add(inspection)
        db.flush()
        hazard = Hazard(inspection_id=inspection.id, hazard_type=kind, title=title,
            description='Historical demonstration observation; not a real inspection.', evidence=['Demo historical field observation'],
            confidence=0.89, severity_score=severity, exposure_score=exposure, probability_score=probability,
            risk_score=risk.final_score, risk_level=risk.risk_level, risk_breakdown=risk.model_dump(mode='json'),
            recommended_actions=['Review the affected area and document corrective work.'], ai_generated=True, created_at=created)
        db.add(hazard)
        db.flush()
        status = ('CLOSED', 'CLOSED', 'RECTIFICATION', 'OPEN', 'UNDER_REVIEW', 'CLOSED')[index % 6]
        closed = created + timedelta(days=2) if status == 'CLOSED' else None
        incident = Incident(incident_code=f'SSI-DEMO-{index + 1:03}', project_id=project.id, site_id=site.id,
            inspection_id=inspection.id, primary_hazard_id=hazard.id, title=title, description=hazard.description,
            risk_score=risk.final_score, risk_level=risk.risk_level, status=status, human_decision='CONFIRMED',
            assigned_to=('Alex Chen', 'Maya Patel', 'Daniel Wong')[index % 3],
            created_at=created, updated_at=closed or created, closed_at=closed,
            deadline=created + timedelta(days=3))
        if closed:
            incident.reinspection_json = MockSafetyAIProvider().analyze_reinspection(
                incident_id=index + 1, previous_risk=risk.final_score, evidence_path=None, notes='Historical demo').model_dump(mode='json')
            incident.rectification_evidence = 'demo://historical-evidence'
        db.add(incident)
        db.flush()
        if closed:
            incident.reinspection_json = {**incident.reinspection_json, 'original_incident_id': incident.id}
        db.add(CorrectiveAction(incident_id=incident.id, action_text=hazard.recommended_actions[0], priority=risk.risk_level,
            assigned_to=incident.assigned_to, status='COMPLETED' if closed else 'PENDING',
            created_at=created, completed_at=closed))
        db.add(AuditLog(entity_type='incident', entity_id=incident.id, action='DEMO_HISTORY_IMPORTED', actor_type='SYSTEM',
            actor_name='Demo seed', new_value={'status': status}, metadata_json={'is_demo': True}, created_at=created))
        if closed:
            db.add(AuditLog(entity_type='incident', entity_id=incident.id, action='CASE_CLOSED_BY_HUMAN', actor_type='HUMAN',
                actor_name=incident.assigned_to, previous_value={'status': 'REINSPECTION'}, new_value={'status': 'CLOSED'},
                metadata_json={'is_demo': True, 'historical_import': True}, created_at=closed))
    demo = Inspection(project_id=project.id, site_id=sites[0].id, location_text='Level 16 · East Facade', source_type='DEMO',
        description='Main competition scenario: review fall protection and the incomplete edge barrier.', created_at=anchor)
    db.add(demo)
    db.flush()
    audit(db, 'inspection', demo.id, 'DEMO_INSPECTION_CREATED', 'Demo seed', 'SYSTEM')
    analyze(db, demo, MockSafetyAIProvider())
    # Leave this inspection awaiting human review, ready to resume from the Inspection page.
    db.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize deterministic SafeSite demonstration data.')
    parser.add_argument('--reset', action='store_true', help='Drop all application tables in the configured database.')
    args = parser.parse_args()
    if args.reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_database(session)
    print('SafeSite demo database ready.' + (' Tables were reset.' if args.reset else ' Existing seed preserved.'))
