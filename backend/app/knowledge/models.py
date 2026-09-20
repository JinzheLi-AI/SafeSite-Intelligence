from datetime import date, datetime
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base, UTCDateTime, utcnow
from app.models.entities import Record

class OfficialDocument(Record, Base):
    __tablename__ = 'official_documents'
    __table_args__ = (UniqueConstraint('source_key', 'checksum', 'embedding_signature', 'parser_version'),)
    source_key: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(300))
    authority: Mapped[str] = mapped_column(String(100))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    document_type: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(String(700))
    catalog_url: Mapped[str] = mapped_column(String(700))
    publication_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[str | None] = mapped_column(String(150))
    language: Mapped[str] = mapped_column(String(30))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    related_source_key: Mapped[str | None] = mapped_column(String(80))
    checksum: Mapped[str] = mapped_column(String(64))
    embedding_signature: Mapped[str] = mapped_column(String(250))
    parser_version: Mapped[str] = mapped_column(String(40))
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime())
    ingested_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    quality_notes: Mapped[list] = mapped_column(JSON, default=list)

class SourceChunk(Record, Base):
    __tablename__ = 'source_chunks'
    __table_args__ = (UniqueConstraint('document_id', 'ordinal'),)
    document_id: Mapped[int] = mapped_column(ForeignKey('official_documents.id'), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(150))
    section_heading: Mapped[str] = mapped_column(String(300))
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    hazard_categories: Mapped[list] = mapped_column(JSON)
    embedding: Mapped[list] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class CitationGrounding(Record, Base):
    __tablename__ = 'citation_groundings'
    citation_id: Mapped[int] = mapped_column(ForeignKey('regulation_citations.id'), unique=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey('source_chunks.id'))
    # Immutable metadata snapshot as retrieved; old citations never silently change after a corpus update.
    evidence_json: Mapped[dict] = mapped_column(JSON)
