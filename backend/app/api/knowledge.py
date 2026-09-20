from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.jurisdictions import project_context, SOURCE_JURISDICTIONS
from app.knowledge.models import OfficialDocument, SourceChunk
from app.knowledge.contracts import RetrievalResult
from app.knowledge.retrieval import search
from app.schemas.contracts import StrictModel, HazardType
from app.models.documents import KnowledgeDocument
from app.repositories.queries import fields

router = APIRouter(prefix='/knowledge',tags=['Verified Safety Knowledge'])
DB = Annotated[Session,Depends(get_db)]

class SearchRequest(StrictModel):
    project_id: int | None = Field(default=None, gt=0)
    query: str = Field(min_length=3,max_length=1000)
    hazard_type: HazardType

@router.get('/context')
def context(db: DB, project_id: int | None = None):
    return project_context(db,project_id)

@router.get('/documents')
def documents(db: DB, include_inactive: bool = False, project_id: int | None = None):
    result = []
    active = project_context(db,project_id)
    source_jurisdiction = SOURCE_JURISDICTIONS.get(active['regulatory_jurisdiction'])
    for doc in db.scalars(select(OfficialDocument).order_by(OfficialDocument.active.desc(),OfficialDocument.id)):
        if doc.jurisdiction != source_jurisdiction or (not include_inactive and not doc.active):
            continue
        result.append({'id':'official-'+str(doc.id),'document_id':doc.id,'document_title':doc.title,
            'authority':doc.authority,'jurisdiction':doc.jurisdiction,'document_type':doc.document_type,
            'source_url':doc.source_url,'source_reference':doc.source_url,'catalog_url':doc.catalog_url,
            'publication_date':doc.publication_date,'effective_date':doc.effective_date,'version':doc.version,
            'verified':doc.verified,'active':doc.active,'is_demo':False,'language':doc.language,
            'retrieved_at':doc.retrieved_at,'ingested_at':doc.ingested_at,'checksum':doc.checksum,
            'embedding_signature':doc.embedding_signature,'related_source_key':doc.related_source_key,
            'chunk_count':db.scalar(select(func.count(SourceChunk.id)).where(SourceChunk.document_id==doc.id)),
            'indexed_chunk_count':db.scalar(select(func.count(SourceChunk.id)).where(SourceChunk.document_id==doc.id,SourceChunk.active.is_(True))),
            'quality_notes':doc.quality_notes,'excerpt':'Official Labour Department source. Open the original document to review its scope and limitations.',
            'section':'','status':'VERIFIED SOURCE' if doc.active else 'INACTIVE / HISTORICAL'})
    result.extend(fields(d) for d in db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id)))
    return result

@router.post('/search',response_model=RetrievalResult)
def search_sources(body: SearchRequest,db: DB):
    return search(db,body.hazard_type,body.query,jurisdiction=project_context(db,body.project_id)['regulatory_jurisdiction'])
