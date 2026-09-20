from datetime import date
from typing import Literal
from pydantic import Field
from app.schemas.contracts import StrictModel, HazardType

DocumentType = Literal['legislation', 'code_of_practice', 'guidance_note', 'safety_guide', 'handbook', 'official_alert']
NO_EVIDENCE = 'No sufficiently relevant verified safety source was retrieved.'

class SourceSpec(StrictModel):
    key: str = Field(pattern=r'^[a-z0-9-]+$')
    title: str
    authority: Literal['Hong Kong Labour Department']
    jurisdiction: Literal['Hong Kong']
    document_type: DocumentType
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_url: str
    catalog_url: str
    hazards: list[HazardType]
    version: str | None
    language: str
    publication_date: date | None
    effective_date: date | None
    active: bool
    related_source_key: str | None
    excluded_sections: list[str]
    retrieval_enabled: bool = True
    index_page_start: int = 1
    index_page_end: int = 300
    verification_date: date

class RegulationEvidence(StrictModel):
    document_id: int
    chunk_id: int
    document_title: str
    document_type: DocumentType
    authority: str
    jurisdiction: Literal['Hong Kong']
    section: str
    section_heading: str
    page_number: int
    excerpt: str
    source_url: str
    version: str | None
    effective_date: date | None
    checksum: str
    retrieval_score: float = Field(ge=0, le=1)
    semantic_score: float = Field(ge=-1, le=1)
    verified: Literal[True] = True
    active: bool
    related_source_key: str | None

class RetrievalResult(StrictModel):
    status: Literal['success', 'no_match', 'unavailable', 'error']
    message: str
    citations: list[RegulationEvidence] = Field(max_length=3)
    candidate_count: int = 0
    latency_ms: int = 0

class KnowledgeError(Exception):
    pass
