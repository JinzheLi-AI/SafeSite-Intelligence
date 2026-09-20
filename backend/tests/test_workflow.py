from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import pytest
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import select, func
from app.ai.mock import MockSafetyAIProvider
from app.ai.provider import get_provider
from app.main import app
from app.models.entities import Hazard, RegulationCitation, Incident, AIExecution, AuditLog, Project, Site, Inspection
from app.schemas.contracts import InspectionAnalysis, ReinspectionAnalysis, RiskLevel
from app.services.risk import RiskEngine
from app.services.guidance import demo_citation

PREFIX = '/api/v1'


def create(client):
    response = client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': 1, 'location_text': 'Level 16 · East Facade'})
    assert response.status_code == 201, response.text
    return response.json()


def analyzed(client):
    item = create(client)
    response = client.post(f'{PREFIX}/inspections/{item["id"]}/analyze')
    assert response.status_code == 200, response.text
    return response.json()


def confirmed(client):
    item = analyzed(client)
    response = client.post(f'{PREFIX}/inspections/{item["id"]}/confirm', json={'assigned_to': 'Alex Chen'})
    assert response.status_code == 201, response.text
    return response.json()[0]


def ready_to_reinspect(client):
    incident = confirmed(client)
    response = client.post(f'{PREFIX}/incidents/{incident["id"]}/start-rectification', json={})
    assert response.status_code == 200
    for action in incident['corrective_actions']:
        response = client.patch(f'{PREFIX}/incidents/{incident["id"]}/actions/{action["id"]}', json={'status': 'COMPLETED'})
        assert response.status_code == 200
    return incident


def test_health(client):
    assert client.get(PREFIX + '/health').json()['status'] == 'ok'


@pytest.mark.parametrize('score,level', [(0,'LOW'),(24,'LOW'),(25,'MEDIUM'),(49,'MEDIUM'),(50,'HIGH'),(79,'HIGH'),(80,'CRITICAL'),(100,'CRITICAL')])
def test_risk_thresholds(score, level):
    assert RiskEngine.level(score) == level


def test_working_at_height_override():
    risk = RiskEngine.assess('working_at_height', 5, 4, 1, 0.94)
    assert risk.raw_score == 20
    assert risk.final_score == 85 and risk.risk_level == 'CRITICAL'
    assert risk.overrides
    assert RiskEngine.assess('working_at_height', 5, 3, 1, 0.94).risk_level == 'LOW'


def test_low_confidence_does_not_discount_risk():
    risk = RiskEngine.assess('unprotected_edge', 5, 4, 4, 0.2)
    assert risk.final_score == 80 and risk.requires_human_review
    value = MockSafetyAIProvider().analyze_inspection(location='Tower A', description=None, image_path=None).model_dump()
    value.update(overall_confidence=0.2, requires_human_review=False)
    assert InspectionAnalysis.model_validate(value).requires_human_review


@pytest.mark.parametrize('inputs', [('housekeeping',6,2,2,.9),('housekeeping',2,6,2,.9),('housekeeping',2,2,5,.9),('housekeeping',2,2,2,1.2),('invented',2,2,2,.9)])
def test_invalid_risk_inputs(inputs):
    with pytest.raises(ValueError):
        RiskEngine.assess(*inputs)


def test_inspection_creation_and_validation(client, db_factory):
    item = create(client)
    assert item['status'] == 'CREATED'
    assert item['created_at'].endswith('Z')
    assert client.get(f'{PREFIX}/inspections/{item["id"]}').json()['location_text'] == item['location_text']
    assert client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': 1, 'location_text': ' '}).status_code == 422
    assert client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': 1, 'location_text': 'East', 'source_type': 'IMAGE'}).status_code == 422
    with db_factory() as db:
        project = Project(name='Other', code='OTHER', location='Demo')
        db.add(project); db.flush()
        site = Site(project_id=project.id, name='Other tower', zone='North')
        db.add(site); db.commit()
        site_id = site.id
    assert client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': site_id, 'location_text': 'East'}).status_code == 422


def test_analysis_persistence_and_idempotency(client, db_factory):
    item = analyzed(client)
    assert len(item['hazards']) == 2
    assert item['analysis_json']['requires_human_review']
    assert item['hazards'][0]['risk_score'] == 85
    assert item['hazards'][1]['risk_score'] == 60
    assert client.post(f'{PREFIX}/inspections/{item["id"]}/analyze').status_code == 200
    with db_factory() as db:
        assert db.scalar(select(func.count(Hazard.id))) == 2
        assert db.scalar(select(func.count(Incident.id))) == 0
        assert db.scalar(select(func.count(AIExecution.id))) == 1
        assert db.scalar(select(func.count(RegulationCitation.id))) == 2
        assert all(not c.verified and c.is_demo for c in db.scalars(select(RegulationCitation)))
        execution = db.scalar(select(AIExecution))
        assert execution.model_provider == 'mock' and execution.prompt_version and execution.policy_version


def test_confirmation_creates_real_incidents_once(client, db_factory):
    item = analyzed(client)
    path = f'{PREFIX}/inspections/{item["id"]}/confirm'
    first = client.post(path, json={})
    second = client.post(path, json={})
    assert first.status_code == second.status_code == 201
    assert [i['id'] for i in first.json()] == [i['id'] for i in second.json()]
    with db_factory() as db:
        assert db.scalar(select(func.count(Incident.id))) == 2
    assert all(i['human_decision'] == 'CONFIRMED' and len(i['corrective_actions']) == 2 for i in first.json())


def test_modify_preserves_original_ai_finding(client):
    item = analyzed(client)
    result = client.post(f'{PREFIX}/inspections/{item["id"]}/confirm', json={
        'decision': 'MODIFIED', 'modified_description': 'Human observed an incomplete barrier; work was stopped.'}).json()[0]
    assert result['human_decision'] == 'MODIFIED'
    assert result['description'] != result['hazard']['description']
    assert result['risk_score'] == 85


def test_rejection_does_not_create_incidents(client, db_factory):
    item = analyzed(client)
    path = f'{PREFIX}/inspections/{item["id"]}'
    assert client.post(path + '/reject', json={}).status_code == 422
    assert client.post(path + '/reject', json={'notes': 'Demonstration observation does not match the reviewed evidence.'}).json()['status'] == 'REJECTED'
    assert client.post(path + '/confirm', json={}).status_code == 409
    with db_factory() as db:
        assert db.scalar(select(func.count(Incident.id))) == 0


def test_incident_cannot_close_without_workflow(client):
    incident = confirmed(client)
    path = f'{PREFIX}/incidents/{incident["id"]}'
    assert client.post(path + '/close', json={}).status_code == 409
    assert client.post(path + '/reinspect', json={'use_demo_evidence': True}).status_code == 409
    assert client.post(path + '/start-rectification', json={}).status_code == 200
    assert client.post(path + '/reinspect', json={'use_demo_evidence': True}).status_code == 409


def test_human_close_after_reinspection_and_audit(client, db_factory):
    incident = ready_to_reinspect(client)
    path = f'{PREFIX}/incidents/{incident["id"]}'
    assert client.post(path + '/reinspect', json={}).status_code == 422
    response = client.post(path + '/reinspect', json={'use_demo_evidence': True, 'notes': 'Demo verified by supervisor'})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['status'] == 'REINSPECTION' and result['closed_at'] is None
    assert result['reinspection_json']['previous_risk_score'] == 85
    assert result['reinspection_json']['current_risk_score'] == 15
    assert client.get(path).json()['status'] == 'REINSPECTION'
    assert client.post(path + '/close', json={'actor_type': 'AI'}).status_code == 422
    response = client.post(path + '/close', json={'actor_name': 'Alex Chen'})
    assert response.status_code == 200
    assert response.json()['status'] == 'CLOSED' and response.json()['closed_at']
    assert client.get(path).json()['status'] == 'CLOSED'
    entries = client.get(path + '/audit').json()
    assert entries[-1]['action'] == 'CASE_CLOSED_BY_HUMAN'
    assert entries[-1]['actor_type'] == 'HUMAN'
    assert any(a['actor_type'] == 'AI' and a['action'] == 'AI_REINSPECTION_COMPLETED' for a in entries)
    assert client.post(path + '/close', json={}).status_code == 409
    assert client.post(path + '/start-rectification', json={}).status_code == 409
    with db_factory() as db:
        assert db.scalar(select(func.count(AIExecution.id))) == 2
        assert db.scalar(select(func.count(AuditLog.id))) >= 9


def test_human_can_override_eligible_reinspection(client):
    incident = ready_to_reinspect(client)
    path = f'{PREFIX}/incidents/{incident["id"]}'
    client.post(path + '/reinspect', json={'use_demo_evidence': True})
    response = client.post(path + '/start-rectification', json={'notes': 'Further work required by human review'})
    assert response.json()['status'] == 'RECTIFICATION'
    assert response.json()['reinspection_json'] is None
    assert all(a['status'] == 'PENDING' for a in response.json()['corrective_actions'])
    assert client.post(path + '/close', json={}).status_code == 409


def test_mock_provider_strict_output():
    provider = MockSafetyAIProvider()
    analysis = provider.analyze_inspection(location='Tower A', description=None, image_path=None)
    assert isinstance(analysis, InspectionAnalysis) and len(analysis.hazards) == 2
    reinspection = provider.analyze_reinspection(incident_id=7, previous_risk=85, evidence_path=None, notes='')
    assert isinstance(reinspection, ReinspectionAnalysis)
    assert reinspection.recommendation == 'ELIGIBLE_FOR_CLOSURE'
    data = reinspection.model_dump(); data['hazard_still_present'] = True
    with pytest.raises(ValidationError):
        ReinspectionAnalysis.model_validate(data)
    assert demo_citation(1, 'missing_ppe') is None


def test_provider_failure_is_persisted_without_partial_hazards(client, db_factory):
    class BrokenProvider(MockSafetyAIProvider):
        def analyze_inspection(self, **kwargs):
            raise RuntimeError('test failure')
    app.dependency_overrides[get_provider] = lambda: BrokenProvider()
    item = create(client)
    response = client.post(f'{PREFIX}/inspections/{item["id"]}/analyze')
    assert response.status_code == 502
    with db_factory() as db:
        assert db.scalar(select(func.count(Hazard.id))) == 0
        assert db.scalar(select(AIExecution)).status == 'FAILED'
        assert db.get(Inspection, item['id']).status == 'CREATED'
    app.dependency_overrides.pop(get_provider)
    assert client.post(f'{PREFIX}/inspections/{item["id"]}/analyze').status_code == 200


def test_business_risk_overrides_provider_score(client):
    class DishonestScoreProvider(MockSafetyAIProvider):
        def analyze_inspection(self, **kwargs):
            result = super().analyze_inspection(**kwargs)
            for hazard in result.hazards:
                hazard.risk_score, hazard.risk_level = 1, RiskLevel.LOW
            return result
    app.dependency_overrides[get_provider] = lambda: DishonestScoreProvider()
    assert analyzed(client)['hazards'][0]['risk_score'] == 85


def test_upload_validation_and_persistence(client):
    assert client.post(PREFIX + '/uploads', files={'file': ('fake.jpg', b'not an image', 'image/jpeg')}).status_code == 415
    buffer = BytesIO()
    Image.new('RGB', (32, 32), '#508d72').save(buffer, format='PNG')
    response = client.post(PREFIX + '/uploads', files={'file': ('evidence.png', buffer.getvalue(), 'image/png')})
    assert response.status_code == 201
    path = response.json()['image_path']
    result = client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': 1, 'location_text': 'Tower A', 'source_type': 'IMAGE', 'image_path': path})
    assert result.status_code == 201 and result.json()['image_path'] == path
    assert client.post(PREFIX + '/inspections', json={'project_id': 1, 'site_id': 1, 'location_text': 'Tower A', 'image_path': '/uploads/../../secret'}).status_code == 422


def test_not_found_and_request_validation(client):
    assert client.get(PREFIX + '/incidents/999').status_code == 404
    assert client.get(PREFIX + '/inspections/999').status_code == 404
    assert client.get(PREFIX + '/incidents?status=INVALID').status_code == 422
    item = create(client)
    assert client.post(f'{PREFIX}/inspections/{item["id"]}/confirm', json={}).status_code == 409


def test_seed_is_repeatable_and_dashboard_matches_database(client, db_factory):
    from app.seed.demo import seed_database
    with db_factory() as db:
        seed_database(db)
        seed_database(db)
        count = db.scalar(select(func.count(Incident.id)))
        assert count == 18
    summary = client.get(PREFIX + '/dashboard/summary').json()
    assert summary['total_incidents'] == 18
    assert summary['open_incidents'] == 9 and summary['resolved_incidents'] == 9
    assert len(client.get(PREFIX + '/knowledge/documents').json()) == 3
    assert all(not d['verified'] and d['is_demo'] for d in client.get(PREFIX + '/knowledge/documents').json())
    assert len(client.get(PREFIX + '/analytics/hazards').json()) == 6
    assert len(client.get(PREFIX + '/analytics/risk-trend').json()) == 14


def test_concurrent_confirmation_is_not_duplicated(client, db_factory):
    item = analyzed(client)
    path = f'{PREFIX}/inspections/{item["id"]}/confirm'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(path, json={}), range(2)))
    assert all(result.status_code in (201, 409) for result in results)
    with db_factory() as db:
        assert db.scalar(select(func.count(Incident.id))) == 2
