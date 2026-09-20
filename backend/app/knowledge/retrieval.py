import logging
import math
import re
import time
from datetime import date
import numpy as np
from sqlalchemy import select
from app.core.config import settings
from app.core.jurisdictions import SOURCE_JURISDICTIONS
from app.db.session import utcnow
from app.knowledge.models import OfficialDocument, SourceChunk, CitationGrounding
from app.knowledge.contracts import RegulationEvidence, RetrievalResult, KnowledgeError, NO_EVIDENCE
from app.knowledge import registry as source_registry
from app.knowledge.embeddings import Embedder
from app.knowledge.concepts import CONCEPTS, tokens
from app.models.entities import RegulationCitation

logger = logging.getLogger(__name__)

def search(db, hazard_type: str, query: str, *, embedder=None, jurisdiction='HK-SAR') -> RetrievalResult:
    started = time.perf_counter()
    query = re.sub(r'\s+',' ',query).strip()[:1500]
    if hazard_type not in CONCEPTS:
        raise KnowledgeError('Unsupported hazard category.')
    embedder = embedder or Embedder()
    result = RetrievalResult(status='no_match',message=NO_EVIDENCE,citations=[])
    try:
        source_jurisdiction = SOURCE_JURISDICTIONS.get(jurisdiction)
        if source_jurisdiction is None:
            result.status = 'unavailable'
            result.message = 'No verified corpus is available for this project jurisdiction. No cross-jurisdiction fallback was used.'
            return result
        documents = list(db.scalars(select(OfficialDocument).where(OfficialDocument.verified.is_(True),
            OfficialDocument.active.is_(True), OfficialDocument.jurisdiction==source_jurisdiction,
            OfficialDocument.embedding_signature==embedder.signature)))
        today = utcnow().date()
        documents = [d for d in documents if d.effective_date is None or d.effective_date<=today]
        registry = {s.key:s for s in source_registry.source_set()}
        present = {d.source_key for d in documents}
        # A current base code is usable only with all registered current amendments indexed.
        documents = [d for d in documents if d.source_key in registry and registry[d.source_key].active
            and registry[d.source_key].source_url == d.source_url
            and registry[d.source_key].version == d.version
            and registry[d.source_key].sha256 == d.checksum
            and all(s.key in present for s in registry.values() if s.related_source_key==d.source_key
                    and s.active and (s.effective_date is None or s.effective_date<=today))]
        by_id = {d.id:d for d in documents}
        if not by_id:
            result.status = 'unavailable'
            result.message = 'Verified knowledge index is unavailable for this embedding model. Ingest the official hk_core source set; no demo evidence was substituted.'
            return result
        chunks = list(db.scalars(select(SourceChunk).where(SourceChunk.document_id.in_(by_id),SourceChunk.active.is_(True))))
        chunks = [c for c in chunks if hazard_type in c.hazard_categories and c.embedding]
        result.candidate_count = len(chunks)
        if not chunks or not tokens(query):
            return result
        vector = np.asarray(embedder.encode([query + '\nRelated concepts: '+', '.join(CONCEPTS[hazard_type][:3])],query=True)[0],dtype=float)
        query_terms = tokens(query)
        candidates = []
        for chunk in chunks:
            values = np.asarray(chunk.embedding,dtype=float)
            if values.shape != vector.shape or not np.isfinite(values).all():
                raise KnowledgeError('Knowledge vector index is inconsistent; rebuild using the configured model.')
            semantic = float(np.dot(vector,values)/(np.linalg.norm(vector)*np.linalg.norm(values)))
            semantic = max(-1.,min(1.,semantic))
            lexical = len(query_terms & tokens(chunk.text+' '+chunk.section_heading)) / min(5,len(query_terms))
            lexical = min(1.,lexical)
            specificity = 1. if re.match(r'^\d+\.',chunk.section) else .4
            score = .75*max(0.,semantic)+.20*lexical+.05*specificity
            low = chunk.text.lower()
            # Prefer operative passages over introductions and measures for a different specific task.
            if any(phrase in low for phrase in ['this overview has been','this code of practice is issued','this handbook is intended']):
                score -= .20
            if low.endswith(':') or 'this leaflet outlines' in low:
                score -= .12
            if 'dismantl' in low and 'dismantl' not in query.lower():
                score -= .12
            if hazard_type in ('working_at_height','unprotected_edge') and 'helmet' in low and 'helmet' not in query.lower():
                score -= .15
            score = max(0.,score)
            # Semantic support AND actual query-term support are required. Expansion alone cannot force a citation.
            if semantic >= settings.retrieval_min_semantic and score >= settings.retrieval_min_score and lexical>0:
                candidates.append((score,semantic,chunk))
        candidates.sort(key=lambda x:(-x[0],x[2].id))
        selected = []
        for score,semantic,chunk in candidates:
            # Diversify near-duplicate passages, without generating any citation text.
            words = tokens(chunk.text)
            if any(len(words & tokens(other.text))/max(1,len(words | tokens(other.text)))>.80 for other in selected):
                continue
            if sum(c.document_id==chunk.document_id for c in selected)>=2:
                continue
            selected.append(chunk)
            doc = by_id[chunk.document_id]
            result.citations.append(RegulationEvidence(document_id=doc.id,chunk_id=chunk.id,
                document_title=doc.title,document_type=doc.document_type,authority=doc.authority,jurisdiction=doc.jurisdiction,
                section=chunk.section,section_heading=chunk.section_heading,page_number=chunk.page_number,
                excerpt=chunk.text,source_url=doc.source_url,version=doc.version,effective_date=doc.effective_date,
                checksum=doc.checksum,retrieval_score=round(score,6),semantic_score=round(semantic,6),
                verified=True,active=doc.active,related_source_key=doc.related_source_key))
            if len(result.citations)==3:
                break
        if result.citations:
            result.status, result.message = 'success','Relevant official safety guidance retrieved. Applicability requires professional review.'
        return result
    except KnowledgeError as exc:
        result.status, result.message = 'unavailable',str(exc)
        return result
    finally:
        result.latency_ms = round((time.perf_counter()-started)*1000)
        logger.info('knowledge_retrieval query=%r hazard=%s candidates=%s selected=%s scores=%s latency_ms=%s status=%s',
            query,hazard_type,result.candidate_count,[c.chunk_id for c in result.citations],
            [c.retrieval_score for c in result.citations],result.latency_ms,result.status)

def persist_evidence(db, hazard_id: int, evidence: RegulationEvidence):
    # Resolve and compare every field to the DB again; no model- or client-authored title/URL/excerpt is trusted.
    chunk = db.get(SourceChunk,evidence.chunk_id)
    doc = db.get(OfficialDocument,evidence.document_id)
    if (not chunk or not doc or chunk.document_id != doc.id or not doc.verified or not doc.active or not chunk.active
        or evidence.excerpt != chunk.text or evidence.document_title != doc.title or evidence.source_url != doc.source_url
        or evidence.section != chunk.section or evidence.page_number != chunk.page_number
        or evidence.checksum != doc.checksum or evidence.document_type != doc.document_type
        or evidence.authority != doc.authority or evidence.jurisdiction != doc.jurisdiction
        or evidence.version != doc.version or evidence.effective_date != doc.effective_date
        or evidence.section_heading != chunk.section_heading or evidence.related_source_key != doc.related_source_key):
        raise KnowledgeError('Citation does not match active stored source evidence.')
    citation = RegulationCitation(hazard_id=hazard_id,document_title=doc.title,section=chunk.section,
        jurisdiction=doc.jurisdiction,excerpt=chunk.text,source_reference=doc.source_url,verified=True,is_demo=False)
    db.add(citation)
    db.flush()
    db.add(CitationGrounding(citation_id=citation.id,chunk_id=chunk.id,evidence_json=evidence.model_dump(mode='json')))
    return citation
