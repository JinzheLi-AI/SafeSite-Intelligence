import logging
import time
from datetime import timedelta
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.ai.accounting import attach
from app.ai.provider import SafetyAIProvider
from app.ai.errors import AIProviderError
from app.ai.images import resolve_upload
from app.core.config import settings
from app.db.session import utcnow
from app.models.entities import Inspection, Hazard, Incident, CorrectiveAction, AuditLog, AIExecution
from app.schemas.contracts import ConfirmFindings, HumanAction, ReinspectRequest, InspectionAnalysis, ReinspectionAnalysis, ReinspectionContext, AnalysisProvenance
from app.services.risk import RiskEngine
from app.services.guidance import demo_citation
from app.knowledge.retrieval import search as retrieve_guidance, persist_evidence
from app.core.jurisdictions import project_context

logger = logging.getLogger(__name__)


def audit(db: Session, entity_type: str, entity_id: int, action: str, actor: str = 'Safety Officer',
          actor_type: str = 'HUMAN', previous: dict | None = None, new: dict | None = None, metadata: dict | None = None):
    db.add(AuditLog(entity_type=entity_type, entity_id=entity_id, action=action,
        actor_type=actor_type, actor_name=actor, previous_value=previous, new_value=new, metadata_json=metadata))


def require_state(record, *states):
    if record.status not in states:
        raise HTTPException(409, f'Cannot perform this action while status is {record.status}. Expected: {", ".join(states)}.')


def valid_evidence(path: str | None):
    if path is not None:
        try:
            resolve_upload(path)
        except AIProviderError as exc:
            raise HTTPException(exc.status_code, exc.message) from None


def latest_analysis_attempt(inspection_id: int):
    return select(AuditLog.id).where(AuditLog.entity_type == 'inspection',
        AuditLog.entity_id == inspection_id, AuditLog.action == 'AI_ANALYSIS_STARTED').order_by(AuditLog.id.desc()).limit(1).scalar_subquery()


def attempt_condition(inspection_id: int, attempt_id: int | None):
    latest = latest_analysis_attempt(inspection_id)
    return latest == attempt_id if attempt_id is not None else latest.is_(None)


def execute_ai(db: Session, provider: SafetyAIProvider, workflow: str, entity_type: str, entity_id: int, call, attempt_id: int | None = None):
    started = time.perf_counter()
    prompt_version = (getattr(provider, 'reinspection_prompt_version', provider.prompt_version)
                      if workflow == 'reinspection-analysis' else provider.prompt_version)
    execution = AIExecution(workflow_name=workflow, entity_type=entity_type, entity_id=entity_id,
        model_provider=provider.model_provider, model_name=provider.model_name, prompt_version=prompt_version,
        policy_version=RiskEngine.POLICY_VERSION, status='RUNNING')
    try:
        result = call()
        if attempt_id is not None:
            # Lock/check ownership before saving observations. Expired responses cannot overwrite a retry.
            owned = db.execute(update(Inspection).where(Inspection.id == entity_id,
                Inspection.status == 'ANALYZING', attempt_condition(entity_id, attempt_id)).values(status='ANALYZING'))
            if owned.rowcount != 1:
                raise AIProviderError('superseded_attempt', 'This analysis attempt expired or was replaced. Refresh to see the current inspection.', 409)
        result.provenance = AnalysisProvenance(kind='DEMO_AI' if provider.model_provider == 'mock' else 'REAL_AI',
            provider=provider.model_provider, model_name=provider.model_name, prompt_version=prompt_version, output_language=getattr(provider, 'output_language', 'en'))
        execution.confidence = getattr(result, 'overall_confidence', getattr(result, 'mitigation_confidence', None))
        execution.status = 'SUCCEEDED'
    except Exception as exc:
        # Never log raw SDK exceptions: they can contain prompt, image or provider response data.
        code = exc.code if isinstance(exc, AIProviderError) else 'provider_validation_failed'
        message = exc.message if isinstance(exc, AIProviderError) else 'AI analysis failed validation. No findings were saved; retry the analysis.'
        status = exc.status_code if isinstance(exc, AIProviderError) else 502
        logger.error('AI workflow failed workflow=%s entity=%s:%s code=%s exception_type=%s',
            workflow, entity_type, entity_id, code, type(exc).__name__)
        db.rollback()
        if entity_type == 'inspection':
            conditions = [Inspection.id == entity_id, Inspection.status == 'ANALYZING']
            if attempt_id is not None:
                conditions.append(attempt_condition(entity_id, attempt_id))
            reset = db.execute(update(Inspection).where(*conditions).values(status='CREATED'))
            if reset.rowcount:
                audit(db, 'inspection', entity_id, 'AI_ANALYSIS_FAILED', 'System', 'SYSTEM',
                    previous={'status': 'ANALYZING'}, new={'status': 'CREATED'},
                    metadata={'attempt_id': attempt_id, 'error_code': code})

        execution.status = 'FAILED'
        execution.error_message = code + ': ' + message
        execution.latency_ms = round((time.perf_counter() - started) * 1000)
        attach(execution,provider)
        db.add(execution)
        db.commit()
        raise HTTPException(status, message) from None
    execution.latency_ms = round((time.perf_counter() - started) * 1000)
    attach(execution,provider,execution.confidence)
    db.add(execution)
    return result

def analyze(db: Session, inspection: Inspection, provider: SafetyAIProvider):
    if inspection.status in ('ANALYZED', 'CONFIRMED', 'MODIFIED', 'REJECTED'):
        return inspection
    if inspection.status == 'ANALYZING':
        attempt = db.scalar(select(AuditLog).where(AuditLog.entity_type == 'inspection',
            AuditLog.entity_id == inspection.id, AuditLog.action == 'AI_ANALYSIS_STARTED').order_by(AuditLog.id.desc()))
        # Legacy interrupted rows have no start event; their creation time is a conservative fallback.
        started_at = attempt.created_at if attempt else inspection.created_at
        stale_seconds = max(300, 2 * settings.ai_timeout_seconds + 60)
        if started_at > utcnow() - timedelta(seconds=stale_seconds):
            raise HTTPException(409, f'Analysis is still in progress. Retry after {int(stale_seconds)} seconds from its start if it was interrupted.')
        recovered = db.execute(update(Inspection).where(Inspection.id == inspection.id,
            Inspection.status == 'ANALYZING', attempt_condition(inspection.id, attempt.id if attempt else None))
            .values(status='CREATED'))
        if recovered.rowcount != 1:
            raise HTTPException(409, 'This inspection changed during recovery. Refresh and retry.')
        audit(db, 'inspection', inspection.id, 'STALE_ANALYSIS_RECOVERED', 'System', 'SYSTEM',
            previous={'status': 'ANALYZING'}, new={'status': 'CREATED'},
            metadata={'expired_attempt_id': attempt.id if attempt else None,
                      'started_at': started_at.isoformat(), 'stale_after_seconds': stale_seconds})
        db.flush()
        inspection.status = 'CREATED'
    require_state(inspection, 'CREATED')
    # Atomic claim prevents simultaneous requests from inserting duplicate hazards.
    claimed = db.execute(update(Inspection).where(Inspection.id == inspection.id, Inspection.status == 'CREATED')
        .values(status='ANALYZING'))
    if claimed.rowcount != 1:
        raise HTTPException(409, 'This inspection is already being analyzed. Refresh the page.')
    attempt = AuditLog(entity_type='inspection', entity_id=inspection.id, action='AI_ANALYSIS_STARTED',
        actor_type='SYSTEM', actor_name='System', previous_value={'status': 'CREATED'},
        new_value={'status': 'ANALYZING'}, metadata_json={'provider': provider.model_provider})
    db.add(attempt)
    db.flush()
    attempt_id = attempt.id
    # Real inference can take seconds: release SQLite's write lock after the atomic claim.
    # Mock/seed calls retain their existing transaction behavior.
    if provider.model_provider != 'mock':
        db.commit()
    result = execute_ai(db, provider, 'inspection-analysis', 'inspection', inspection.id,
        lambda: InspectionAnalysis.model_validate(provider.analyze_inspection(location=inspection.location_text,
            description=inspection.description, image_path=inspection.image_path).model_dump()), attempt_id=attempt_id)
    for finding in result.hazards:
        # Recompute from primitive factors. Never trust a provider's final score.
        risk = RiskEngine.assess(finding.hazard_type, finding.severity, finding.exposure, finding.probability, finding.confidence)
        finding.risk_score, finding.risk_level = risk.final_score, risk.risk_level
        hazard = Hazard(inspection_id=inspection.id, hazard_type=finding.hazard_type, title=finding.title,
            description=finding.description, evidence=finding.visual_evidence, confidence=finding.confidence,
            severity_score=finding.severity, exposure_score=finding.exposure, probability_score=finding.probability,
            risk_score=risk.final_score, risk_level=risk.risk_level, risk_breakdown=risk.model_dump(mode='json'),
            recommended_actions=finding.recommended_actions, ai_generated=True)
        db.add(hazard)
        db.flush()
        # Demo citations are available only for the explicitly mock provider.
        citation = demo_citation(hazard.id, hazard.hazard_type) if provider.model_provider == 'mock' else None
        if citation:
            db.add(citation)
        if provider.model_provider != 'mock':
            query = ' '.join([finding.title, finding.description, *finding.visual_evidence, *finding.regulation_queries])[:1500]
            try:
                with db.begin_nested():
                    guidance = retrieve_guidance(db, finding.hazard_type, query, jurisdiction=project_context(db, inspection.project_id)['regulatory_jurisdiction'])
                    for evidence in guidance.citations:
                        persist_evidence(db,hazard.id,evidence)
                    audit(db,'hazard',hazard.id,'SAFETY_GUIDANCE_RETRIEVAL','Knowledge retrieval','SYSTEM',
                        metadata={'query':query,'hazard_type':finding.hazard_type,'status':guidance.status,
                                  'message':guidance.message,'candidate_count':guidance.candidate_count,
                                  'chunk_ids':[c.chunk_id for c in guidance.citations],
                                  'scores':[c.retrieval_score for c in guidance.citations],'latency_ms':guidance.latency_ms})
            except Exception as exc:
                # Retrieval fails independently; vision findings, deterministic risk and human review remain usable.
                logger.error('knowledge_retrieval_failed hazard_id=%s exception_type=%s',hazard.id,type(exc).__name__)
                audit(db,'hazard',hazard.id,'SAFETY_GUIDANCE_RETRIEVAL','Knowledge retrieval','SYSTEM',
                    metadata={'status':'error','message':'Verified safety retrieval failed. No source was substituted.'})

    result.requires_human_review = result.requires_human_review or bool(result.hazards)
    inspection.analysis_json = result.model_dump(mode='json')
    inspection.status = 'ANALYZED'
    inspection.completed_at = utcnow()
    audit(db, 'inspection', inspection.id, 'AI_ANALYSIS_COMPLETED', provider.model_name, 'AI',
        previous={'status': 'CREATED'}, new={'status': 'ANALYZED'}, metadata={'human_review_required': result.requires_human_review, 'analysis_source': result.provenance.model_dump()})
    db.flush()
    return inspection


def confirm_inspection(db: Session, inspection: Inspection, request: ConfirmFindings) -> list[Incident]:
    if inspection.status in ('CONFIRMED', 'MODIFIED'):
        return list(db.scalars(select(Incident).where(Incident.inspection_id == inspection.id).order_by(Incident.id)))
    require_state(inspection, 'ANALYZED')
    claimed = db.execute(update(Inspection).where(Inspection.id == inspection.id, Inspection.status == 'ANALYZED')
        .values(status=request.decision))
    if claimed.rowcount != 1:
        raise HTTPException(409, 'Findings were already reviewed. Refresh the page.')
    hazards = list(db.scalars(select(Hazard).where(Hazard.inspection_id == inspection.id).order_by(Hazard.id)))
    if not hazards:
        raise HTTPException(409, 'No hazards to confirm.')
    result = []
    for hazard in hazards:
        incident = Incident(incident_code=f'SSI-{uuid4().hex[:10].upper()}', project_id=inspection.project_id,
            site_id=inspection.site_id, inspection_id=inspection.id, primary_hazard_id=hazard.id, title=hazard.title,
            description=request.modified_description if request.decision == 'MODIFIED' else hazard.description,
            risk_score=hazard.risk_score, risk_level=hazard.risk_level, status='OPEN',
            assigned_to=request.assigned_to, deadline=request.deadline, human_decision=request.decision)
        db.add(incident)
        db.flush()
        for action in hazard.recommended_actions:
            db.add(CorrectiveAction(incident_id=incident.id, action_text=action, priority=hazard.risk_level, assigned_to=request.assigned_to))
        audit(db, 'incident', incident.id, 'FINDINGS_CONFIRMED' if request.decision == 'CONFIRMED' else 'FINDINGS_MODIFIED_AND_CONFIRMED',
            request.actor_name, new={'status': 'OPEN', 'human_decision': request.decision},
            metadata={'notes': request.notes, 'inspection_id': inspection.id, 'original_description': hazard.description,
                      'accepted_description': incident.description})
        result.append(incident)
    inspection.status = request.decision
    inspection.review_notes = request.notes
    audit(db, 'inspection', inspection.id, 'HUMAN_CONFIRMED_FINDINGS', request.actor_name,
        new={'incident_ids': [i.id for i in result], 'decision': request.decision})
    db.flush()
    return result


def reject_inspection(db: Session, inspection: Inspection, request: HumanAction):
    require_state(inspection, 'ANALYZED')
    if not request.notes.strip():
        raise HTTPException(422, 'Please give a reason for rejecting the findings.')
    claimed = db.execute(update(Inspection).where(Inspection.id == inspection.id, Inspection.status == 'ANALYZED')
        .values(status='REJECTED', review_notes=request.notes))
    if claimed.rowcount != 1:
        raise HTTPException(409, 'Findings were already reviewed.')
    audit(db, 'inspection', inspection.id, 'FINDINGS_REJECTED', request.actor_name,
        new={'status': 'REJECTED'}, metadata={'notes': request.notes})
    db.flush()
    return inspection


def transition(db: Session, incident: Incident, status: str, request: HumanAction, action: str):
    previous = {'status': incident.status, 'human_decision': incident.human_decision}
    incident.status = status
    incident.updated_at = utcnow()
    audit(db, 'incident', incident.id, action, request.actor_name, previous=previous,
          new={'status': status, 'human_decision': incident.human_decision}, metadata={'notes': request.notes})
    db.flush()
    return incident


def confirm_incident(db: Session, incident: Incident, request: ConfirmFindings):
    require_state(incident, 'OPEN', 'UNDER_REVIEW')
    previous = {'description': incident.description, 'human_decision': incident.human_decision}
    incident.human_decision = request.decision
    incident.assigned_to = request.assigned_to
    incident.deadline = request.deadline
    if request.decision == 'MODIFIED':
        incident.description = request.modified_description
    for action in db.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident.id)):
        action.assigned_to = request.assigned_to
    audit(db, 'incident', incident.id, 'HUMAN_REVIEW_UPDATED', request.actor_name, previous=previous,
        new={'description': incident.description, 'human_decision': request.decision}, metadata={'notes': request.notes})
    return transition(db, incident, 'OPEN', request, 'INCIDENT_CONFIRMED')


def reject_incident(db: Session, incident: Incident, request: HumanAction):
    require_state(incident, 'OPEN', 'UNDER_REVIEW')
    if not request.notes.strip():
        raise HTTPException(422, 'A rejection reason is required.')
    previous_decision = incident.human_decision
    incident.human_decision = 'REJECTED'
    audit(db, 'incident', incident.id, 'HUMAN_DECISION_OVERRIDDEN', request.actor_name,
        previous={'human_decision': previous_decision}, new={'human_decision': 'REJECTED'})
    return transition(db, incident, 'REJECTED', request, 'INCIDENT_REJECTED')


def start_rectification(db: Session, incident: Incident, request: HumanAction):
    require_state(incident, 'OPEN', 'UNDER_REVIEW', 'REINSPECTION')
    if incident.human_decision not in ('CONFIRMED', 'MODIFIED'):
        raise HTTPException(409, 'Human confirmation is required before rectification.')
    if incident.status == 'REINSPECTION':
        incident.reinspection_json = None
        for action in db.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident.id)):
            action.status, action.completed_at = 'PENDING', None
    return transition(db, incident, 'RECTIFICATION', request, 'RECTIFICATION_STARTED')


def reinspect(db: Session, incident: Incident, request: ReinspectRequest, provider: SafetyAIProvider):
    require_state(incident, 'RECTIFICATION')
    actions = list(db.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident.id)))
    if not actions or any(a.status != 'COMPLETED' for a in actions):
        raise HTTPException(409, 'Complete all corrective actions before reinspection.')
    if request.use_demo_evidence and provider.model_provider != 'mock':
        raise HTTPException(422, 'Demo evidence is available only with the mock provider.')
    if not request.evidence_path and not request.use_demo_evidence:
        raise HTTPException(422, 'Upload evidence or explicitly select demonstration evidence.')
    valid_evidence(request.evidence_path)
    hazard = db.get(Hazard, incident.primary_hazard_id)
    original = db.get(Inspection, incident.inspection_id)
    context = ReinspectionContext(hazard_type=hazard.hazard_type, title=hazard.title,
        description=hazard.description, evidence=hazard.evidence, image_path=original.image_path)

    def evaluate():
        value = ReinspectionAnalysis.model_validate(provider.analyze_reinspection(incident_id=incident.id,
            previous_risk=incident.risk_score, evidence_path=request.evidence_path, notes=request.notes,
            original_hazard=context).model_dump())
        if value.original_incident_id != incident.id or value.previous_risk_score != incident.risk_score:
            raise AIProviderError('inconsistent_reinspection', 'Reinspection output does not match this incident.')
        if provider.model_provider != 'mock':
            if value.current_risk_breakdown is None:
                raise AIProviderError('missing_risk_factors', 'Real reinspection must include current risk factors.')
            factors = value.current_risk_breakdown
            risk = RiskEngine.assess(hazard.hazard_type, factors.severity, factors.exposure, factors.probability,
                                    value.mitigation_confidence)
            value.current_risk_score, value.current_risk_breakdown = risk.final_score, risk
            if risk.final_score >= 25 and value.recommendation == 'ELIGIBLE_FOR_CLOSURE':
                value.recommendation = 'HUMAN_REVIEW'
        return ReinspectionAnalysis.model_validate(value.model_dump())

    result = execute_ai(db, provider, 'reinspection-analysis', 'incident', incident.id, evaluate)
    incident.reinspection_json = result.model_dump(mode='json')
    incident.rectification_evidence = request.evidence_path or 'demo://rectification-evidence'
    incident.rectification_notes = request.notes
    audit(db, 'incident', incident.id, 'AI_REINSPECTION_COMPLETED', provider.model_name, 'AI',
        new=result.model_dump(mode='json'), metadata={'demo_evidence': request.use_demo_evidence})
    return transition(db, incident, 'REINSPECTION', request, 'EVIDENCE_SUBMITTED_FOR_REVIEW')


def close_incident(db: Session, incident: Incident, request: HumanAction):
    require_state(incident, 'REINSPECTION')
    result = incident.reinspection_json
    if incident.human_decision not in ('CONFIRMED', 'MODIFIED') or not result:
        raise HTTPException(409, 'Human confirmation and successful reinspection are required.')
    validated = ReinspectionAnalysis.model_validate(result)
    if validated.recommendation != 'ELIGIBLE_FOR_CLOSURE':
        raise HTTPException(409, 'Reinspection has not established closure eligibility.')
    actions = list(db.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident.id)))
    if not actions or any(a.status != 'COMPLETED' for a in actions):
        raise HTTPException(409, 'All corrective actions must be completed.')
    incident.closed_at = utcnow()
    # Only the explicit human command calls this. AI providers never receive a session.
    return transition(db, incident, 'CLOSED', request, 'CASE_CLOSED_BY_HUMAN')
