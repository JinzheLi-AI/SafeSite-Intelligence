from datetime import datetime, date
from enum import StrEnum
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class HazardType(StrEnum):
    MISSING_PPE = 'missing_ppe'
    WORKING_AT_HEIGHT = 'working_at_height'
    UNPROTECTED_EDGE = 'unprotected_edge'
    UNSAFE_SCAFFOLDING = 'unsafe_scaffolding'
    ELECTRICAL_HAZARD = 'electrical_hazard'
    HOUSEKEEPING = 'housekeeping'


class RiskLevel(StrEnum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class IncidentStatus(StrEnum):
    OPEN = 'OPEN'
    UNDER_REVIEW = 'UNDER_REVIEW'
    RECTIFICATION = 'RECTIFICATION'
    REINSPECTION = 'REINSPECTION'
    CLOSED = 'CLOSED'
    REJECTED = 'REJECTED'


class HumanDecision(StrEnum):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    REJECTED = 'REJECTED'
    MODIFIED = 'MODIFIED'


Confidence = Annotated[float, Field(ge=0, le=1)]
Score = Annotated[int, Field(ge=0, le=100)]
NonEmpty = Annotated[str, Field(min_length=1, max_length=4000)]


class AnalysisProvenance(StrictModel):
    output_language: Literal['en', 'zh-CN'] | None = None
    kind: Literal['REAL_AI', 'DEMO_AI', 'UNKNOWN'] = 'UNKNOWN'
    provider: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None


class ReinspectionContext(StrictModel):
    hazard_type: HazardType
    title: str
    description: str
    evidence: list[str]
    image_path: str | None = None


class HazardAnalysis(StrictModel):
    hazard_type: HazardType
    title: Annotated[str, Field(min_length=1, max_length=250)]
    description: NonEmpty
    visual_evidence: list[NonEmpty]
    confidence: Confidence
    severity: Annotated[int, Field(ge=1, le=5)]
    exposure: Annotated[int, Field(ge=1, le=5)]
    probability: Annotated[int, Field(ge=1, le=4)]
    risk_score: Score
    risk_level: RiskLevel
    recommended_actions: list[NonEmpty]
    regulation_queries: list[NonEmpty]


class InspectionAnalysis(StrictModel):
    summary: NonEmpty
    hazards: list[HazardAnalysis] = Field(max_length=30)
    overall_confidence: Confidence
    requires_human_review: bool
    model_uncertainty_review: bool | None = None
    operational_human_confirmation: bool | None = None
    reasoning_notes: list[NonEmpty]
    provenance: AnalysisProvenance | None = None

    @model_validator(mode='after')
    def enforce_review(self):
        # Legacy objects retain unknown (null) split signals. V2 signals may never
        # bypass the existing operational or low-confidence guardrails.
        split = self.model_uncertainty_review is not None or self.operational_human_confirmation is not None
        if split:
            if self.model_uncertainty_review is None or self.operational_human_confirmation is None:
                raise ValueError('Both split review signals must be supplied together')
            if self.overall_confidence < 0.85 or any(h.confidence < 0.85 or not h.visual_evidence for h in self.hazards):
                self.model_uncertainty_review = True
            if self.hazards:
                self.operational_human_confirmation = True
            self.requires_human_review = self.requires_human_review or self.model_uncertainty_review or self.operational_human_confirmation
        # All findings require review; low confidence is never interpreted as safe.
        if self.hazards or self.overall_confidence < 0.85:
            self.requires_human_review = True
        return self


class ReinspectionAnalysis(StrictModel):
    original_incident_id: int = Field(gt=0)
    hazard_still_present: bool
    mitigation_confidence: Confidence
    evidence: list[NonEmpty] = Field(min_length=1)
    previous_risk_score: Score
    current_risk_score: Score
    recommendation: Literal['KEEP_OPEN', 'HUMAN_REVIEW', 'ELIGIBLE_FOR_CLOSURE']
    provenance: AnalysisProvenance | None = None
    current_risk_breakdown: 'RiskBreakdown | None' = None

    @model_validator(mode='after')
    def safe_recommendation(self):
        if self.recommendation == 'ELIGIBLE_FOR_CLOSURE' and (
            self.hazard_still_present or self.mitigation_confidence < 0.8 or self.current_risk_score >= 25
        ):
            raise ValueError('Closure eligibility requires mitigated hazard, confidence >= 0.8 and risk < 25')
        return self


class InspectionCreate(StrictModel):
    project_id: int = Field(gt=0)
    site_id: int = Field(gt=0)
    location_text: Annotated[str, Field(min_length=1, max_length=300)]
    source_type: Literal['IMAGE', 'DEMO'] = 'DEMO'
    image_path: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=4000)


class HumanAction(StrictModel):
    actor_name: Annotated[str, Field(min_length=1, max_length=100)] = 'Safety Officer'
    notes: str = Field(default='', max_length=4000)


class ConfirmFindings(HumanAction):
    decision: Literal['CONFIRMED', 'MODIFIED'] = 'CONFIRMED'
    assigned_to: Annotated[str, Field(min_length=1, max_length=100)] = 'Safety Officer'
    deadline: AwareDatetime | None = None
    modified_description: NonEmpty | None = None

    @model_validator(mode='after')
    def modification_required(self):
        if self.decision == 'MODIFIED' and not self.modified_description:
            raise ValueError('A modified description is required for Modify / Confirm')
        return self


class ReinspectRequest(HumanAction):
    evidence_path: str | None = Field(default=None, max_length=500)
    use_demo_evidence: bool = False


class ActionUpdate(HumanAction):
    status: Literal['PENDING', 'COMPLETED']


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SiteOut(ORMResponse):
    id: int
    project_id: int
    name: str
    zone: str
    created_at: datetime


class ProjectOut(ORMResponse):
    regulatory_jurisdiction: str = 'HK-SAR'
    id: int
    name: str
    code: str
    location: str
    status: str
    created_at: datetime
    sites: list[SiteOut]


class CitationOut(ORMResponse):
    chunk_id: int | None = None
    document_id: int | None = None
    document_type: str | None = None
    authority: str | None = None
    section_heading: str | None = None
    page_number: int | None = None
    source_url: str | None = None
    version: str | None = None
    effective_date: date | None = None
    checksum: str | None = None
    retrieval_score: float | None = None
    active: bool | None = None
    related_source_key: str | None = None
    id: int
    document_title: str
    section: str
    jurisdiction: str
    excerpt: str
    source_reference: str
    verified: bool
    is_demo: bool


class RiskBreakdown(StrictModel):
    severity: int
    exposure: int
    probability: int
    raw_score: int
    final_score: int
    risk_level: RiskLevel
    confidence: Confidence
    requires_human_review: bool
    policy_version: str
    overrides: list[str]
    formula: str


class HazardOut(ORMResponse):
    guidance_message: str | None = None
    id: int
    hazard_type: HazardType
    title: str
    description: str
    evidence: list[str]
    confidence: float
    severity_score: int
    exposure_score: int
    probability_score: int
    risk_score: int
    risk_level: RiskLevel
    risk_breakdown: RiskBreakdown
    recommended_actions: list[str]
    ai_generated: bool
    citations: list[CitationOut]


class InspectionOut(ORMResponse):
    analysis_source: AnalysisProvenance
    id: int
    project_id: int
    site_id: int
    location_text: str
    source_type: str
    image_path: str | None
    description: str | None
    status: str
    created_at: datetime
    completed_at: datetime | None
    analysis_json: InspectionAnalysis | None
    review_notes: str | None
    hazards: list[HazardOut]
    incident_ids: list[int]


class ActionOut(ORMResponse):
    id: int
    action_text: str
    priority: str
    assigned_to: str
    status: str
    created_at: datetime
    completed_at: datetime | None


class IncidentOut(ORMResponse):
    analysis_source: AnalysisProvenance
    reinspection_source: AnalysisProvenance
    id: int
    incident_code: str
    project_id: int
    site_id: int
    inspection_id: int
    primary_hazard_id: int
    title: str
    description: str
    risk_score: int
    risk_level: RiskLevel
    status: IncidentStatus
    assigned_to: str
    deadline: datetime | None
    human_decision: HumanDecision
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    reinspection_json: ReinspectionAnalysis | None
    rectification_evidence: str | None
    rectification_notes: str | None
    project_name: str
    site_name: str
    location_text: str
    image_path: str | None
    hazard: HazardOut
    corrective_actions: list[ActionOut]


class AuditOut(ORMResponse):
    id: int
    entity_type: str
    entity_id: int
    action: str
    actor_type: str
    actor_name: str
    previous_value: dict | None
    new_value: dict | None
    metadata_json: dict | None
    created_at: datetime
