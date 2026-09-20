from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.entities import Project, Site, Inspection, Hazard, RegulationCitation, Incident, CorrectiveAction, AIExecution, AuditLog
from app.schemas.contracts import AnalysisProvenance
from app.knowledge.models import CitationGrounding


def get_or_404(db: Session, model, record_id: int):
    result = db.get(model, record_id)
    if result is None:
        raise HTTPException(404, f'{model.__name__} {record_id} not found')
    return result


def fields(record) -> dict:
    return {column.key: getattr(record, column.key) for column in record.__table__.columns}


def hazard_view(db: Session, hazard: Hazard) -> dict:
    citations = []
    for citation in db.scalars(select(RegulationCitation).where(RegulationCitation.hazard_id == hazard.id)):
        grounding = db.scalar(select(CitationGrounding).where(CitationGrounding.citation_id==citation.id))
        value = fields(citation)
        if grounding:
            value.update(grounding.evidence_json)
        elif not citation.is_demo:
            value['verified'] = False
        citations.append(value)
    event = db.scalar(select(AuditLog).where(AuditLog.entity_type=='hazard',AuditLog.entity_id==hazard.id,
        AuditLog.action=='SAFETY_GUIDANCE_RETRIEVAL').order_by(AuditLog.id.desc()))
    return {**fields(hazard),'citations':citations,
            'guidance_message':event.metadata_json.get('message') if event and event.metadata_json else None}



def analysis_source(db: Session, entity_type: str, entity_id: int, result: dict | None) -> AnalysisProvenance:
    if result and result.get('provenance'):
        return AnalysisProvenance.model_validate(result['provenance'])
    execution = db.scalar(select(AIExecution).where(AIExecution.entity_type == entity_type,
        AIExecution.entity_id == entity_id, AIExecution.status == 'SUCCEEDED').order_by(AIExecution.id.desc()))
    if execution:
        return AnalysisProvenance(kind='DEMO_AI' if execution.model_provider == 'mock' else 'REAL_AI',
            provider=execution.model_provider, model_name=execution.model_name, prompt_version=execution.prompt_version)
    # Do not infer source from a filename, source_type or current configuration.
    return AnalysisProvenance()


def inspection_view(db: Session, inspection: Inspection) -> dict:
    return {**fields(inspection), 'analysis_source': analysis_source(db, 'inspection', inspection.id, inspection.analysis_json),
        'hazards': [hazard_view(db, h) for h in db.scalars(select(Hazard).where(Hazard.inspection_id == inspection.id).order_by(Hazard.id))],
        'incident_ids': list(db.scalars(select(Incident.id).where(Incident.inspection_id == inspection.id).order_by(Incident.id)))}


def incident_view(db: Session, incident: Incident) -> dict:
    inspection = get_or_404(db, Inspection, incident.inspection_id)
    return {**fields(incident),
        'analysis_source': analysis_source(db, 'inspection', inspection.id, inspection.analysis_json),
        'reinspection_source': analysis_source(db, 'incident', incident.id, incident.reinspection_json),
        'project_name': get_or_404(db, Project, incident.project_id).name,
        'site_name': get_or_404(db, Site, incident.site_id).name, 'location_text': inspection.location_text,
        'image_path': inspection.image_path,
        'hazard': hazard_view(db, get_or_404(db, Hazard, incident.primary_hazard_id)),
        'corrective_actions': list(db.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident.id).order_by(CorrectiveAction.id)))}
