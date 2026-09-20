from typing import Annotated
from pydantic import Field, StrictBool, StrictFloat, StrictInt
from app.schemas.contracts import StrictModel, HazardType, NonEmpty


class VisualFactors(StrictModel):
    severity: Annotated[StrictInt, Field(ge=1, le=5)]
    exposure: Annotated[StrictInt, Field(ge=1, le=5)]
    probability: Annotated[StrictInt, Field(ge=1, le=4)]


class VisualHazardCandidate(VisualFactors):
    hazard_type: HazardType
    title: Annotated[str, Field(min_length=1, max_length=250)]
    description: NonEmpty
    visual_evidence: list[NonEmpty] = Field(max_length=20)
    confidence: Annotated[StrictFloat, Field(ge=0, le=1)]
    recommended_actions: list[NonEmpty] = Field(min_length=1, max_length=10)
    regulation_queries: list[NonEmpty] = Field(max_length=10)


class VisualInspectionOutput(StrictModel):
    summary: NonEmpty
    hazards: list[VisualHazardCandidate] = Field(max_length=30)
    overall_confidence: Annotated[StrictFloat, Field(ge=0, le=1)]
    requires_human_review: StrictBool
    ambiguity_detected: StrictBool
    reasoning_notes: list[NonEmpty] = Field(max_length=30)


class VisualReinspectionOutput(VisualFactors):
    hazard_still_present: StrictBool
    mitigation_confidence: Annotated[StrictFloat, Field(ge=0, le=1)]
    evidence: list[NonEmpty] = Field(min_length=1, max_length=20)
    same_location_supported: StrictBool
    mitigation_visually_supported: StrictBool
    ambiguity_detected: StrictBool
    reasoning_notes: list[NonEmpty] = Field(max_length=20)
