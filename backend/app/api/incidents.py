from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.provider import SafetyAIProvider, get_reinspection_provider
from app.db.session import get_db, utcnow
from app.models.entities import Incident, AuditLog, CorrectiveAction
from app.repositories.queries import get_or_404, incident_view
from app.schemas.contracts import IncidentOut, HumanAction, ConfirmFindings, ReinspectRequest, AuditOut, ActionUpdate, IncidentStatus, RiskLevel
from app.services import workflow

router = APIRouter(prefix='/incidents', tags=['Incidents'])
DB = Annotated[Session, Depends(get_db)]
AI = Annotated[SafetyAIProvider, Depends(get_reinspection_provider)]


@router.get('', response_model=list[IncidentOut])
def list_incidents(db: DB, status: IncidentStatus | None = None, risk_level: RiskLevel | None = None,
                   limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)):
    query = select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())
    if status:
        query = query.where(Incident.status == status)
    if risk_level:
        query = query.where(Incident.risk_level == risk_level)
    return [incident_view(db, row) for row in db.scalars(query.limit(limit).offset(offset))]


@router.get('/{incident_id}', response_model=IncidentOut)
def get_incident(incident_id: int, db: DB):
    return incident_view(db, get_or_404(db, Incident, incident_id))


@router.post('/{incident_id}/confirm', response_model=IncidentOut)
def confirm(incident_id: int, body: ConfirmFindings, db: DB):
    return incident_view(db, workflow.confirm_incident(db, get_or_404(db, Incident, incident_id), body))


@router.post('/{incident_id}/reject', response_model=IncidentOut)
def reject(incident_id: int, body: HumanAction, db: DB):
    return incident_view(db, workflow.reject_incident(db, get_or_404(db, Incident, incident_id), body))


@router.post('/{incident_id}/start-rectification', response_model=IncidentOut)
def start_rectification(incident_id: int, body: HumanAction, db: DB):
    return incident_view(db, workflow.start_rectification(db, get_or_404(db, Incident, incident_id), body))


@router.post('/{incident_id}/reinspect', response_model=IncidentOut)
def reinspect(incident_id: int, body: ReinspectRequest, db: DB, provider: AI):
    return incident_view(db, workflow.reinspect(db, get_or_404(db, Incident, incident_id), body, provider))


@router.post('/{incident_id}/close', response_model=IncidentOut)
def close(incident_id: int, body: HumanAction, db: DB):
    return incident_view(db, workflow.close_incident(db, get_or_404(db, Incident, incident_id), body))


@router.patch('/{incident_id}/actions/{action_id}', response_model=IncidentOut)
def update_action(incident_id: int, action_id: int, body: ActionUpdate, db: DB):
    incident = get_or_404(db, Incident, incident_id)
    workflow.require_state(incident, 'RECTIFICATION')
    action = get_or_404(db, CorrectiveAction, action_id)
    if action.incident_id != incident.id:
        raise HTTPException(404, 'Corrective action not found on this incident.')
    previous = action.status
    action.status = body.status
    action.completed_at = utcnow() if body.status == 'COMPLETED' else None
    incident.updated_at = utcnow()
    workflow.audit(db, 'incident', incident.id, 'CORRECTIVE_ACTION_UPDATED', body.actor_name,
        previous={'status': previous}, new={'status': body.status}, metadata={'action_id': action.id, 'notes': body.notes})
    db.flush()
    return incident_view(db, incident)


@router.get('/{incident_id}/audit', response_model=list[AuditOut])
def audit(incident_id: int, db: DB):
    get_or_404(db, Incident, incident_id)
    return list(db.scalars(select(AuditLog).where(AuditLog.entity_type == 'incident', AuditLog.entity_id == incident_id)
        .order_by(AuditLog.created_at, AuditLog.id)))
