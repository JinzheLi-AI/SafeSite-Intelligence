from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.provider import get_provider, SafetyAIProvider
from app.db.session import get_db
from app.models.entities import Inspection, Project, Site
from app.repositories.queries import get_or_404, inspection_view, incident_view
from app.schemas.contracts import InspectionCreate, InspectionOut, IncidentOut, ConfirmFindings, HumanAction
from app.services import workflow

router = APIRouter(prefix='/inspections', tags=['Inspections'])
DB = Annotated[Session, Depends(get_db)]
AI = Annotated[SafetyAIProvider, Depends(get_provider)]


@router.get('', response_model=list[InspectionOut])
def list_inspections(db: DB, limit: int = Query(100, ge=1, le=200)):
    return [inspection_view(db, row) for row in db.scalars(select(Inspection).order_by(Inspection.created_at.desc(), Inspection.id.desc()).limit(limit))]


@router.post('', response_model=InspectionOut, status_code=201)
def create_inspection(body: InspectionCreate, db: DB):
    get_or_404(db, Project, body.project_id)
    site = get_or_404(db, Site, body.site_id)
    if site.project_id != body.project_id:
        raise HTTPException(422, 'The selected site does not belong to this project.')
    workflow.valid_evidence(body.image_path)
    if body.source_type == 'IMAGE' and not body.image_path:
        raise HTTPException(422, 'Image inspections require an uploaded image.')
    item = Inspection(**body.model_dump())
    db.add(item)
    db.flush()
    workflow.audit(db, 'inspection', item.id, 'INSPECTION_CREATED', new={'status': 'CREATED'})
    return inspection_view(db, item)


@router.get('/{inspection_id}', response_model=InspectionOut)
def get_inspection(inspection_id: int, db: DB):
    return inspection_view(db, get_or_404(db, Inspection, inspection_id))


@router.post('/{inspection_id}/analyze', response_model=InspectionOut)
def analyze(inspection_id: int, db: DB, provider: AI):
    return inspection_view(db, workflow.analyze(db, get_or_404(db, Inspection, inspection_id), provider))


@router.post('/{inspection_id}/confirm', response_model=list[IncidentOut], status_code=201)
def confirm(inspection_id: int, body: ConfirmFindings, db: DB):
    return [incident_view(db, item) for item in workflow.confirm_inspection(db, get_or_404(db, Inspection, inspection_id), body)]


@router.post('/{inspection_id}/reject', response_model=InspectionOut)
def reject(inspection_id: int, body: HumanAction, db: DB):
    return inspection_view(db, workflow.reject_inspection(db, get_or_404(db, Inspection, inspection_id), body))
