import json
import re
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

HAZARDS = ('missing_ppe', 'working_at_height', 'unprotected_edge', 'unsafe_scaffolding', 'electrical_hazard', 'housekeeping')
Hazard = Literal['missing_ppe', 'working_at_height', 'unprotected_edge', 'unsafe_scaffolding', 'electrical_hazard', 'housekeeping']
VERIFIED = 'VERIFIED RESULT'
PENDING = 'PENDING LIVE EVALUATION'
MOCKED = 'MOCKED/UNIT-TEST RESULT'

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')

class HazardCase(Record):
    case_id: str
    image_path: str | None = None
    description: str
    ground_truth_hazards: list[Hazard] | None = None
    notes: str = ''
    ambiguous: bool | None = None
    expected_human_review: bool | None = None
    jurisdiction: str = 'HK-SAR'
    label_status: Literal['placeholder', 'draft', 'reviewed'] = 'placeholder'
    image_sha256: str | None = None
    group_id: str | None = None
    reviewers: list[str] = Field(default_factory=list)
    license_or_consent: str | None = None

    @model_validator(mode='after')
    def reviewed(self):
        if self.label_status == 'reviewed' and (not self.image_path or self.ground_truth_hazards is None
            or self.ambiguous is None or self.expected_human_review is None or not self.image_sha256
            or not self.group_id or len({r.strip() for r in self.reviewers if r.strip()}) < 2 or not self.license_or_consent):
            raise ValueError('Reviewed cases require image/hash, labels, ambiguity/review, group, consent and two reviewers.')
        if self.label_status == 'reviewed' and not re.fullmatch(r'[a-fA-F0-9]{64}', self.image_sha256 or ''):
            raise ValueError('Reviewed images require an actual SHA-256 hex digest')
        if self.ground_truth_hazards is not None and len(set(self.ground_truth_hazards)) != len(self.ground_truth_hazards):
            raise ValueError('Duplicate hazard labels')
        return self

class Prediction(Record):
    case_id: str
    hazards: list[Hazard]
    requires_human_review: bool
    uncertain: bool | None = None
    error: str | None = None

class RagCase(Record):
    query_id: str
    hazard_type: Hazard
    query: str
    expected_document_ids: list[str] = Field(default_factory=list)
    expected_source_families: list[str] = Field(default_factory=list)
    expected_section_keywords: list[str] = Field(default_factory=list)
    should_return_evidence: bool
    jurisdiction: str = 'HK-SAR'
    label_status: Literal['draft', 'reviewed'] = 'draft'
    notes: str = ''

    @model_validator(mode='after')
    def targets(self):
        if self.should_return_evidence and not (self.expected_document_ids or self.expected_source_families):
            raise ValueError('Answerable queries require relevance judgments')
        if not self.should_return_evidence and (self.expected_document_ids or self.expected_source_families):
            raise ValueError('No-answer queries cannot have relevant sources')
        return self

def load(path, schema):
    rows = [schema.model_validate(row) for row in json.loads(Path(path).read_text(encoding='utf-8-sig'))]
    ids = [getattr(row, 'case_id', getattr(row, 'query_id', None)) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate dataset IDs')
    return rows
