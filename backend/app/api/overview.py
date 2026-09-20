from collections import Counter
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.db.session import get_db, utcnow
from app.core.config import settings
from app.models.entities import Project, Site, Incident, Hazard, AIExecution
from app.repositories.queries import fields, incident_view
from app.schemas.contracts import ProjectOut, IncidentOut
from app.models.documents import KnowledgeDocument

router = APIRouter(tags=['Overview'])
DB = Annotated[Session, Depends(get_db)]


class Summary(BaseModel):
    safety_risk_score: int
    open_incidents: int
    critical_incidents: int
    resolved_incidents: int
    total_incidents: int
    closure_rate: float
    recent_incidents: list[IncidentOut]
    score_definition: str


@router.get('/health')
def health(db: DB):
    db.execute(text('SELECT 1'))
    from app.ai.capabilities import readiness
    vision=readiness(settings,'vision');reinspection=readiness(settings,'reinspection')
    return {'status':'ok','service':'SafeSite Intelligence','ai_mode':'mock' if vision['provider']=='mock' else 'real',
        'ai_ready':vision['ready'],'vision_model':vision['model'],'ai_error':vision['error'],
        'vision':vision,'reinspection':reinspection}


@router.get('/projects', response_model=list[ProjectOut])
def projects(db: DB):
    return [{**fields(p), 'sites': list(db.scalars(select(Site).where(Site.project_id == p.id).order_by(Site.id)))}
        for p in db.scalars(select(Project).order_by(Project.id))]


@router.get('/dashboard/summary', response_model=Summary)
def summary(db: DB):
    rows = list(db.scalars(select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())))
    active = [i for i in rows if i.status not in ('CLOSED', 'REJECTED')]
    closed = [i for i in rows if i.status == 'CLOSED']
    eligible = [i for i in rows if i.status != 'REJECTED']
    return {'safety_risk_score': round(sum(i.risk_score for i in active) / len(active)) if active else 0,
        'open_incidents': len(active), 'critical_incidents': sum(i.risk_level == 'CRITICAL' for i in active),
        'resolved_incidents': len(closed), 'total_incidents': len(rows),
        'closure_rate': round(len(closed) / len(eligible) * 100, 1) if eligible else 0,
        'recent_incidents': [incident_view(db, i) for i in rows[:5]],
        'score_definition': 'Mean initial risk score of active incidents; higher means more risk. Rejected cases excluded from closure rate.'}


@router.get('/analytics/hazards')
def hazards(db: DB):
    counts = Counter(db.scalars(select(Hazard.hazard_type)))
    return [{'hazard_type': key, 'name': key.replace('_', ' ').title(), 'count': count} for key, count in counts.most_common()]


@router.get('/analytics/risk-trend')
def risk_trend(db: DB):
    rows = list(db.scalars(select(Incident)))
    today = utcnow().date()
    result = []
    for delta in range(13, -1, -1):
        day = today - timedelta(days=delta)
        # End-of-day snapshots reconstructed from creation and terminal timestamps.
        active = [i for i in rows if i.created_at.date() <= day
                  and (i.closed_at is None or i.closed_at.date() > day)
                  and not (i.status == 'REJECTED' and i.updated_at.date() <= day)]
        result.append({'date': day.isoformat(), 'risk_score': round(sum(i.risk_score for i in active) / len(active)) if active else 0,
                       'open_incidents': len(active)})
    return result


@router.get('/ai/executions')
def executions(db: DB):
    return [fields(i) for i in db.scalars(select(AIExecution).order_by(AIExecution.created_at.desc(), AIExecution.id.desc()).limit(50))]
