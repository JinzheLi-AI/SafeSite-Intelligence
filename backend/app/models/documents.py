from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.entities import Record


class KnowledgeDocument(Record, Base):
    __tablename__ = 'knowledge_documents'
    document_title: Mapped[str] = mapped_column(String(250))
    section: Mapped[str] = mapped_column(String(100))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    document_type: Mapped[str] = mapped_column(String(100))
    excerpt: Mapped[str] = mapped_column(Text)
    source_reference: Mapped[str] = mapped_column(String(500), unique=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(50), default='DEMO / UNVERIFIED')
