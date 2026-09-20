from datetime import timedelta
import pytest
from sqlalchemy import select, func
from fastapi import HTTPException
from app.ai.mock import MockSafetyAIProvider
from app.ai.errors import AIProviderError
from app.db.session import utcnow
from app.models.entities import Inspection, AuditLog, Hazard
from app.services import workflow
from app.main import app
from app.ai.provider import get_provider

class OfflineReal(MockSafetyAIProvider):
    model_provider = 'openai'

def create(client):
    return client.post('/api/v1/inspections', json={'project_id':1,'site_id':1,'location_text':'Preserved site','description':'Preserved context'}).json()['id']

def interrupt(db, ident, age=301, legacy=False):
    item = db.get(Inspection, ident)
    item.status = 'ANALYZING'
    if legacy:
        item.created_at = utcnow() - timedelta(seconds=age)
    else:
        db.add(AuditLog(entity_type='inspection', entity_id=ident, action='AI_ANALYSIS_STARTED',
            actor_type='SYSTEM', actor_name='System', created_at=utcnow()-timedelta(seconds=age)))
    db.commit()

@pytest.mark.parametrize('legacy', [False,True])
def test_stale_attempt_retries_without_losing_metadata(client, db_factory, legacy):
    ident = create(client)
    with db_factory() as db:
        interrupt(db,ident,legacy=legacy)
    app.dependency_overrides[get_provider] = OfflineReal
    response = client.post(f'/api/v1/inspections/{ident}/analyze')
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'ANALYZED'
    assert response.json()['location_text'] == 'Preserved site'
    assert response.json()['description'] == 'Preserved context'
    with db_factory() as db:
        assert db.scalar(select(func.count(Hazard.id))) == 2
        assert db.scalar(select(AuditLog).where(AuditLog.action=='STALE_ANALYSIS_RECOVERED'))
    assert client.post(f'/api/v1/inspections/{ident}/analyze').json()['hazards'] == response.json()['hazards']

def test_fresh_attempt_not_stolen(client, db_factory):
    ident = create(client)
    with db_factory() as db:
        interrupt(db,ident,age=30)
    response = client.post(f'/api/v1/inspections/{ident}/analyze')
    assert response.status_code == 409
    with db_factory() as db:
        assert db.get(Inspection,ident).status == 'ANALYZING'
        assert db.scalar(select(func.count(Hazard.id))) == 0

def test_failure_then_retry_records_audit(client, db_factory):
    class Broken(OfflineReal):
        def analyze_inspection(self, **kwargs):
            raise AIProviderError('timeout','Provider timed out',504)
    ident = create(client)
    app.dependency_overrides[get_provider] = Broken
    assert client.post(f'/api/v1/inspections/{ident}/analyze').status_code == 504
    with db_factory() as db:
        assert db.get(Inspection,ident).status == 'CREATED'
        assert db.scalar(select(AuditLog).where(AuditLog.action=='AI_ANALYSIS_FAILED'))
    app.dependency_overrides[get_provider] = OfflineReal
    assert client.post(f'/api/v1/inspections/{ident}/analyze').status_code == 200

@pytest.mark.parametrize('late_failure', [False,True])
def test_expired_response_cannot_overwrite_new_attempt(client, db_factory, late_failure):
    ident = create(client)
    class Delayed(OfflineReal):
        def analyze_inspection(self, **kwargs):
            with db_factory() as other:
                attempt = other.scalar(select(AuditLog).where(AuditLog.action=='AI_ANALYSIS_STARTED'))
                attempt.created_at = utcnow()-timedelta(minutes=6)
                other.commit()
                workflow.analyze(other,other.get(Inspection,ident),OfflineReal())
                other.commit()
            if late_failure:
                raise AIProviderError('timeout','Old request timeout',504)
            return super().analyze_inspection(**kwargs)
    app.dependency_overrides[get_provider] = Delayed
    response = client.post(f'/api/v1/inspections/{ident}/analyze')
    assert response.status_code == (504 if late_failure else 409)
    with db_factory() as db:
        assert db.get(Inspection,ident).status == 'ANALYZED'
        assert db.scalar(select(func.count(Hazard.id))) == 2

def test_start_timestamp_persisted_before_inference(client, db_factory):
    ident = create(client)
    class InspectStart(OfflineReal):
        def analyze_inspection(self, **kwargs):
            with db_factory() as other:
                assert other.get(Inspection,ident).status == 'ANALYZING'
                event = other.scalar(select(AuditLog).where(AuditLog.action=='AI_ANALYSIS_STARTED'))
                assert event and event.created_at <= utcnow()
            return super().analyze_inspection(**kwargs)
    app.dependency_overrides[get_provider] = InspectStart
    assert client.post(f'/api/v1/inspections/{ident}/analyze').status_code == 200
