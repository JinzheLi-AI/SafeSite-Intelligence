from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base, UTCDateTime, utcnow


class Record:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Project(Record, Base):
    __tablename__ = 'projects'
    regulatory_jurisdiction: Mapped[str] = mapped_column(String(20), default='HK-SAR', server_default='HK-SAR')
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    location: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default='ACTIVE')


class Site(Record, Base):
    __tablename__ = 'sites'
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    zone: Mapped[str] = mapped_column(String(100))


class Inspection(Record, Base):
    __tablename__ = 'inspections'
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    site_id: Mapped[int] = mapped_column(ForeignKey('sites.id'))
    location_text: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(30))
    image_path: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='CREATED')
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    analysis_json: Mapped[dict | None] = mapped_column(JSON)
    review_notes: Mapped[str | None] = mapped_column(Text)


class Hazard(Record, Base):
    __tablename__ = 'hazards'
    __table_args__ = (CheckConstraint('confidence >= 0 AND confidence <= 1'), CheckConstraint('risk_score >= 0 AND risk_score <= 100'))
    inspection_id: Mapped[int] = mapped_column(ForeignKey('inspections.id'), index=True)
    hazard_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    severity_score: Mapped[int] = mapped_column(Integer)
    exposure_score: Mapped[int] = mapped_column(Integer)
    probability_score: Mapped[int] = mapped_column(Integer)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    risk_breakdown: Mapped[dict] = mapped_column(JSON)
    recommended_actions: Mapped[list] = mapped_column(JSON)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)


class RegulationCitation(Record, Base):
    __tablename__ = 'regulation_citations'
    hazard_id: Mapped[int] = mapped_column(ForeignKey('hazards.id'), index=True)
    document_title: Mapped[str] = mapped_column(String(250))
    section: Mapped[str] = mapped_column(String(100))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    excerpt: Mapped[str] = mapped_column(Text)
    source_reference: Mapped[str] = mapped_column(String(500))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Incident(Record, Base):
    __tablename__ = 'incidents'
    __table_args__ = (UniqueConstraint('primary_hazard_id'),)
    incident_code: Mapped[str] = mapped_column(String(50), unique=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    site_id: Mapped[int] = mapped_column(ForeignKey('sites.id'))
    inspection_id: Mapped[int] = mapped_column(ForeignKey('inspections.id'))
    primary_hazard_id: Mapped[int] = mapped_column(ForeignKey('hazards.id'))
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default='OPEN', index=True)
    assigned_to: Mapped[str] = mapped_column(String(100), default='Safety Officer')
    deadline: Mapped[datetime | None] = mapped_column(UTCDateTime())
    human_decision: Mapped[str] = mapped_column(String(30), default='PENDING')
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    reinspection_json: Mapped[dict | None] = mapped_column(JSON)
    rectification_evidence: Mapped[str | None] = mapped_column(String(500))
    rectification_notes: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {'version_id_col': version}


class CorrectiveAction(Record, Base):
    __tablename__ = 'corrective_actions'
    incident_id: Mapped[int] = mapped_column(ForeignKey('incidents.id'), index=True)
    action_text: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20))
    assigned_to: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default='PENDING')
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class AuditLog(Record, Base):
    __tablename__ = 'audit_logs'
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_name: Mapped[str] = mapped_column(String(100))
    previous_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)


class AIExecution(Record, Base):
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float)
    call_records: Mapped[list | None] = mapped_column(JSON)
    __tablename__ = 'ai_executions'
    workflow_name: Mapped[str] = mapped_column(String(100))
    model_provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    policy_version: Mapped[str] = mapped_column(String(50))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30))
    error_message: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(Integer)
