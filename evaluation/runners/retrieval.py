"""Ablations use the same vectors and expanded queries; product search is untouched."""
import hashlib
import json
import math
from sqlalchemy import select
from app.knowledge.models import OfficialDocument, SourceChunk
from app.knowledge import registry as source_registry
from app.knowledge.retrieval import search
from app.knowledge.embeddings import Embedder
from app.knowledge.concepts import CONCEPTS
from app.core.jurisdictions import SOURCE_JURISDICTIONS
from app.db.session import utcnow
from evaluation.schema import VERIFIED, PENDING
from evaluation.metrics import retrieval

BASELINES=['semantic_only','semantic_metadata','safesite']

class CachedEmbedder:
    def __init__(self,delegate): self.delegate=delegate;self.cache={}
    @property
    def signature(self):return self.delegate.signature
    def encode(self,texts,**kwargs):
        result=[]
        for value in texts:
            key=(value,kwargs.get('query',False))
            if key not in self.cache:self.cache[key]=self.delegate.encode([value],**kwargs)[0]
            result.append(list(self.cache[key]))
        return result

def eligible(documents,chunks,case,signature):
    registry={s.key:s for s in source_registry.source_set()};today=utcnow().date()
    docs=[d for d in documents if d.verified and d.active and d.jurisdiction==SOURCE_JURISDICTIONS.get(case.jurisdiction)
          and d.embedding_signature==signature and (d.effective_date is None or d.effective_date<=today)]
    present={d.source_key for d in docs}
    ids={d.id for d in docs if d.source_key in registry and registry[d.source_key].active
         and registry[d.source_key].source_url==d.source_url and registry[d.source_key].version==d.version
         and registry[d.source_key].sha256==d.checksum
         and all(s.key in present for s in registry.values() if s.related_source_key==d.source_key and s.active
                 and (s.effective_date is None or s.effective_date<=today))}
    return [c for c in chunks if c.document_id in ids and c.active and case.hazard_type in c.hazard_categories and c.embedding]

def citation(chunk,doc,score):
    return dict(chunk_id=chunk.id,document_id=doc.id,document_key=doc.source_key,family=doc.related_source_key or doc.source_key,
        section=chunk.section,excerpt=chunk.text,source_url=doc.source_url,checksum=doc.checksum,
        document_title=doc.title,score=score,stored_source_valid=True,verified=bool(doc.verified and doc.active and chunk.active))

def stored_valid(item,db):
    chunk=db.get(SourceChunk,item['chunk_id']);doc=db.get(OfficialDocument,item['document_id'])
    return bool(chunk and doc and chunk.document_id==doc.id and item['excerpt']==chunk.text
        and item['section']==chunk.section and item['source_url']==doc.source_url and item['checksum']==doc.checksum
        and item['document_title']==doc.title)

def run(cases,db,embedder=None):
    embedder=CachedEmbedder(embedder or Embedder())
    docs=list(db.scalars(select(OfficialDocument).order_by(OfficialDocument.id)))
    chunks=list(db.scalars(select(SourceChunk).order_by(SourceChunk.id)))
    by_id={d.id:d for d in docs}
    # All baselines use the operational index, not superseded or deliberately excluded vectors.
    compatible=[c for c in chunks if c.embedding and c.active and by_id[c.document_id].active
                and by_id[c.document_id].embedding_signature==embedder.signature]
    corpus={'documents':[{'key':d.source_key,'checksum':d.checksum,'active':d.active,'verified':d.verified,
                        'jurisdiction':d.jurisdiction,'signature':d.embedding_signature,'version':d.version,'source_url':d.source_url,
                        'effective_date':str(d.effective_date),'related_source_key':d.related_source_key} for d in docs],
            'chunks':[{'id':c.id,'document_id':c.document_id,'text':c.text,'section':c.section,'active':c.active,
                       'hazards':c.hazard_categories,'embedding':c.embedding,'section_heading':c.section_heading,'page_number':c.page_number} for c in chunks]}
    fingerprint=hashlib.sha256(json.dumps(corpus,sort_keys=True).encode()).hexdigest()
    if not compatible:
        return {'status':PENDING,'reason':'No compatible stored embeddings; no fabricated retrieval scores.','baselines':{},'corpus_sha256':fingerprint}
    runs={name:[] for name in BASELINES}
    for case in cases:
        for name in BASELINES:
            row={'query_id':case.query_id,'citations':[],'error':None}
            try:
                if name=='safesite':
                    result=search(db,case.hazard_type,case.query,embedder=embedder,jurisdiction=case.jurisdiction)
                    row['retrieval_status']=result.status
                    # Unsupported context is deliberate abstention. Index/embedding failure is not no-answer success.
                    if result.status=='unavailable' and case.jurisdiction in SOURCE_JURISDICTIONS:raise RuntimeError(result.message)
                    for c in result.citations:
                        d=by_id[c.document_id]
                        value=citation(db.get(SourceChunk,c.chunk_id),d,c.retrieval_score)
                        value.update(excerpt=c.excerpt,section=c.section,document_title=c.document_title,
                                     source_url=c.source_url,checksum=c.checksum)
                        row['citations'].append(value)
                else:
                    pool=compatible if name=='semantic_only' else eligible(docs,chunks,case,embedder.signature)
                    if pool:
                        query=case.query+'\nRelated concepts: '+', '.join(CONCEPTS[case.hazard_type][:3])
                        vector=embedder.encode([query],query=True)[0]
                        scored=[]
                        for chunk in pool:
                            values=chunk.embedding
                            if len(vector)!=len(values):raise ValueError('Incompatible vector dimension')
                            denominator=math.sqrt(sum(x*x for x in vector)*sum(x*x for x in values))
                            if not denominator:raise ValueError('Zero norm vector')
                            score=sum(x*y for x,y in zip(vector,values))/denominator
                            if not math.isfinite(score):raise ValueError('Non-finite vector score')
                            scored.append((score,chunk))
                        scored.sort(key=lambda v:(-v[0],v[1].id))
                        row['citations']=[citation(c,by_id[c.document_id],s) for s,c in scored[:3]]
                for item in row['citations']:item['stored_source_valid']=stored_valid(item,db)
            except Exception as exc:
                row['error']=type(exc).__name__;row['citations']=[]
            runs[name].append(row)
    result={name:{'status':VERIFIED,'metrics':retrieval(cases,rows),'rows':rows} for name,rows in runs.items()}
    return {'status':VERIFIED,'basis':'Actual local corpus and embeddings; draft author-curated source-family judgments, not an independently labeled benchmark.',
            'corpus_sha256':fingerprint,'document_count':len(docs),'active_document_count':sum(d.active for d in docs),'stored_chunks':len(chunks),'compatible_vectors':len(compatible),
            'embedding_signature':embedder.signature,'query_expansion':'Identical hazard expansion for all baselines',
            'baselines':result}
