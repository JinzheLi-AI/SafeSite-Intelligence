import hashlib
from datetime import timedelta
from unittest.mock import Mock
import numpy as np
import pymupdf
import pytest
from sqlalchemy import select, func
from app.db.session import utcnow
from app.core.config import settings
from app.knowledge import ingest, chunking
from app.knowledge.chunking import Passage
from app.knowledge.contracts import KnowledgeError, NO_EVIDENCE
from app.knowledge import registry
from app.knowledge.registry import require_registered, official_url

def source_set(*args):
 return registry.source_set(*args)
from app.knowledge.models import OfficialDocument, SourceChunk, CitationGrounding
from app.knowledge.retrieval import search, persist_evidence
from app.knowledge.concepts import CONCEPTS
from app.knowledge.embeddings import Embedder
from app.models.entities import Hazard, RegulationCitation, Incident
from app.services import workflow
from app.ai.mock import MockSafetyAIProvider
from app.ai.provider import get_provider
from app.main import app

# Synthetic fixtures exercise plumbing, never serve as production official documents.
TEXT = {
 'working_at_height':'Workers near an open edge should use suitable working platforms and fall protection. A safety harness and fall arrest system should be inspected before work at height.',
 'unprotected_edge':'Guardrails and edge protection should protect open edges and floor openings. Provide fencing and safe access to each working platform.',
 'missing_ppe':'Workers should wear a safety helmet and suitable personal protective equipment. Inspect the helmet before use and ensure the helmet fits the worker.',
 'unsafe_scaffolding':'Metal and bamboo scaffolds should have safe working platforms. Inspect scaffold bracing and putlogs and ensure scaffolding components are properly supported.',
 'electrical_hazard':'Electrical equipment should be inspected. Replace damaged power cords and protect live electrical parts against contact to prevent electric shock.',
 'housekeeping':'Keep access routes and passages clear of obstructions. Remove rubbish and keep the site tidy. Good housekeeping prevents blocked access and trip hazards.',
}
class FixtureEmbedder:
 signature = 'fixture-semantic-v1'
 def encode(self,texts,**kwargs):
  vectors = []
  for text in texts:
   low = text.lower()
   values = [float(any(term in low for term in CONCEPTS[h])) for h in TEXT]
   if not any(values): values[-1]=.01
   vectors.append(values)
  return vectors

@pytest.fixture
def indexed(db_factory,monkeypatch):
 embedder=FixtureEmbedder()
 approved=[s.model_copy(update={'sha256':hashlib.sha256(b'%PDF-fixture-'+s.key.encode()).hexdigest()}) for s in source_set()]
 monkeypatch.setattr(registry,'source_set',lambda *args:approved)
 def fixture_extract(data,spec):
  selected=[Passage('1.1','Fixture observation',spec.index_page_start,TEXT[str(h)], [str(h)],True) for h in spec.hazards]
  return selected,[]
 monkeypatch.setattr(ingest,'extract',fixture_extract)
 with db_factory() as db:
  for spec in source_set():
   ingest.ingest_document(db,spec,b'%PDF-fixture-'+spec.key.encode(),utcnow(),embedder)
  db.commit()
 return embedder

def test_ingestion_idempotent(indexed,db_factory):
 with db_factory() as db:
  before=db.scalar(select(func.count(SourceChunk.id)))
  spec=source_set()[0]
  doc,changed=ingest.ingest_document(db,spec,b'%PDF-fixture-'+spec.key.encode(),utcnow(),indexed)
  assert not changed and doc.verified
  assert db.scalar(select(func.count(SourceChunk.id)))==before

@pytest.mark.parametrize('url',['https://example.com/fake.pdf','http://www.labour.gov.hk/eng/public/a.pdf',
 'https://www.labour.gov.hk.evil.test/eng/public/a.pdf','https://user@www.labour.gov.hk/eng/public/a.pdf',
 'https://www.labour.gov.hk/eng/public/../secret','file:///tmp/fake.pdf'])
def test_nonofficial_url_rejected(url):
 with pytest.raises(KnowledgeError): official_url(url)

def test_official_domain_alone_not_registration():
 spec=source_set()[0].model_copy(update={'source_url':'https://www.labour.gov.hk/eng/public/arbitrary.pdf'})
 with pytest.raises(KnowledgeError): require_registered(spec)
 with pytest.raises(KnowledgeError): source_set('other')

def test_chunk_metadata_and_grounding(indexed,db_factory):
 with db_factory() as db:
  result=search(db,'working_at_height',TEXT['working_at_height'],embedder=indexed)
  assert result.status=='success'
  for c in result.citations:
   doc=db.get(OfficialDocument,c.document_id);chunk=db.get(SourceChunk,c.chunk_id)
   assert c.document_title==doc.title and c.authority==doc.authority
   assert c.source_url==doc.source_url and c.section==chunk.section and c.excerpt==chunk.text
   assert c.page_number==chunk.page_number and c.checksum==doc.checksum
   assert c.document_type==doc.document_type and c.version==doc.version

@pytest.mark.parametrize('hazard',list(TEXT))
def test_hazard_filter_retrieves_relevant_source(indexed,db_factory,hazard):
 with db_factory() as db:
  result=search(db,hazard,TEXT[hazard],embedder=indexed)
  assert result.status=='success',result
  assert 0<len(result.citations)<=3
  assert all(hazard in db.get(SourceChunk,c.chunk_id).hazard_categories for c in result.citations)

def test_irrelevant_query_returns_no_citation(indexed,db_factory):
 with db_factory() as db:
  result=search(db,'working_at_height','galaxies and tomato soup recipes',embedder=indexed)
  assert result.citations==[] and result.message==NO_EVIDENCE

def test_inactive_unverified_future_filtered(indexed,db_factory):
 with db_factory() as db:
  docs=list(db.scalars(select(OfficialDocument)))
  for i,d in enumerate(docs):
   if i%3==0:d.active=False
   elif i%3==1:d.verified=False
   else:d.effective_date=utcnow().date()+timedelta(days=30)
  db.flush()
  assert search(db,'working_at_height',TEXT['working_at_height'],embedder=indexed).citations==[]

def test_missing_current_addendum_blocks_base(indexed,db_factory):
 with db_factory() as db:
  db.scalar(select(OfficialDocument).where(OfficialDocument.source_key=='metal-addendum')).active=False
  db.flush()
  result=search(db,'unsafe_scaffolding',TEXT['unsafe_scaffolding'],embedder=indexed)
  ids={d.id for d in db.scalars(select(OfficialDocument).where(OfficialDocument.source_key=='metal'))}
  assert all(c.document_id not in ids for c in result.citations)

def test_revision_preserves_old_chunks_and_deactivates_old_document(indexed,db_factory,monkeypatch):
 with db_factory() as db:
  spec=source_set()[0]; old=db.scalar(select(OfficialDocument).where(OfficialDocument.source_key==spec.key))
  old_id=old.id
  updated=spec.model_copy(update={'sha256':hashlib.sha256(b'%PDF-new-revision').hexdigest()})
  approved=[updated if s.key==spec.key else s for s in source_set()]
  monkeypatch.setattr(registry,'source_set',lambda *args:approved)
  new,changed=ingest.ingest_document(db,updated,b'%PDF-new-revision',utcnow(),indexed)
  assert changed and new.id!=old_id and new.active
  assert not db.get(OfficialDocument,old_id).active
  assert db.scalar(select(func.count(SourceChunk.id)).where(SourceChunk.document_id==old_id))>0

def test_rebuild_idempotent_chunk_ids(indexed,db_factory):
 with db_factory() as db:
  spec=source_set()[0]
  original=list(db.scalars(select(SourceChunk.id).order_by(SourceChunk.id)))
  ingest.ingest_document(db,spec,b'%PDF-fixture-'+spec.key.encode(),utcnow(),indexed,rebuild=True)
  assert original==list(db.scalars(select(SourceChunk.id).order_by(SourceChunk.id)))

def test_embedding_failure_does_not_partially_activate_revision(indexed,db_factory):
 class Broken(FixtureEmbedder):
  def encode(self,*args,**kwargs):raise KnowledgeError('Unavailable fixture embedding')
 with db_factory() as db:
  before=db.scalar(select(func.count(OfficialDocument.id)))
  with pytest.raises(KnowledgeError):
   ingest.ingest_document(db,source_set()[0],b'%PDF-new',utcnow(),Broken())
  assert db.scalar(select(func.count(OfficialDocument.id)))==before

@pytest.mark.parametrize("repeat", [1, 2])
def test_real_workflow_retrieval_risk_and_human_controls(client,db_factory,indexed,monkeypatch,repeat):
 class OfflineVision(MockSafetyAIProvider):model_provider='openai'
 app.dependency_overrides[get_provider]=OfflineVision
 monkeypatch.setattr(workflow,'retrieve_guidance',lambda db,h,q,**context:search(db,h,q,embedder=indexed,**context))
 item=client.post('/api/v1/inspections',json={'project_id':1,'site_id':1,'location_text':'Fixture site'}).json()
 path=f"/api/v1/inspections/{item['id']}"
 response=client.post(path+'/analyze')
 assert response.status_code==200,response.text
 result=response.json()
 assert result['analysis_source']['kind']=='REAL_AI'
 assert result['hazards'][0]['risk_score']==85 and result['hazards'][1]['risk_score']==60
 citations=[c for h in result['hazards'] for c in h['citations']]
 assert citations and all(c['verified'] and not c['is_demo'] and c['chunk_id'] for c in citations)
 with db_factory() as db:
  assert db.scalar(select(func.count(Incident.id)))==0
  assert db.scalar(select(func.count(CitationGrounding.id)))==len(citations)
 response=client.post(path+'/confirm',json={})
 assert response.status_code==201
 from app.ai.provider import get_reinspection_provider
 app.dependency_overrides[get_reinspection_provider]=MockSafetyAIProvider
 incident=response.json()[0];route=f"/api/v1/incidents/{incident['id']}"
 assert client.post(route+'/close',json={}).status_code==409
 assert client.post(route+'/start-rectification',json={}).status_code==200
 for action in incident['corrective_actions']:
  assert client.patch(route+f"/actions/{action['id']}",json={'status':'COMPLETED'}).status_code==200
 result=client.post(route+'/reinspect',json={'use_demo_evidence':True,'notes':'Offline fixture, simulated mitigation only.'})
 assert result.status_code==200 and result.json()['status']=='REINSPECTION'
 assert client.post(route+'/close',json={'actor_type':'AI'}).status_code==422
 assert client.post(route+'/close',json={'actor_name':'Offline acceptance reviewer'}).status_code==200
 assert client.get(route).json()['status']=='CLOSED'
 audit=client.get(route+'/audit').json()
 assert audit[-1]['action']=='CASE_CLOSED_BY_HUMAN'
 assert any(a['action']=='AI_REINSPECTION_COMPLETED' for a in audit)
 with db_factory() as db:
  assert db.scalar(select(func.count(CitationGrounding.id)))==len(citations)

def test_retrieval_error_does_not_break_safety_workflow(client,monkeypatch):
 class OfflineVision(MockSafetyAIProvider):model_provider='openai'
 app.dependency_overrides[get_provider]=OfflineVision
 def broken(*args):raise RuntimeError('fixture retrieval failure')
 monkeypatch.setattr(workflow,'retrieve_guidance',broken)
 ident=client.post('/api/v1/inspections',json={'project_id':1,'site_id':1,'location_text':'Fixture site'}).json()['id']
 response=client.post(f'/api/v1/inspections/{ident}/analyze')
 assert response.status_code==200,response.text
 result=response.json()
 assert result['hazards'][0]['risk_score']==85
 assert all(not h['citations'] for h in result['hazards'])
 assert 'failed' in result['hazards'][0]['guidance_message']
 assert client.post(f'/api/v1/inspections/{ident}/confirm',json={}).status_code==201

@pytest.mark.parametrize('field,value',[('document_title','Invented law'),('source_url','https://evil.test'),
 ('section','99.99'),('excerpt','Invented requirement'),('page_number',99),('document_type','legislation')])
def test_forged_citation_metadata_rejected(indexed,db_factory,field,value):
 with db_factory() as db:
  evidence=search(db,'missing_ppe',TEXT['missing_ppe'],embedder=indexed).citations[0]
  with pytest.raises(KnowledgeError):persist_evidence(db,1,evidence.model_copy(update={field:value}))

def test_max_three_and_duplicate_suppression(indexed,db_factory):
 with db_factory() as db:
  result=search(db,'unsafe_scaffolding',TEXT['unsafe_scaffolding'],embedder=indexed)
  assert len(result.citations)<=3
  assert len({c.excerpt for c in result.citations})==len(result.citations)

def test_missing_remote_embedding_key_fails(monkeypatch):
 monkeypatch.setattr(settings,'embedding_provider','openai')
 monkeypatch.setattr(settings,'openai_api_key',None)
 with pytest.raises(KnowledgeError,match='OPENAI_API_KEY'):
  Embedder().encode(['helmet'])

def test_native_parser_preserves_numbered_clause_and_continuation():
 spec=source_set()[0]
 pdf=pymupdf.open()
 for _ in range(spec.index_page_start):pdf.new_page()
 page=pdf[-1]
 page.insert_text((60,70),'4.1 Fall protection')
 page.insert_text((60,110),'Workers should keep working platforms clear and inspect fall protection before use.')
 page.insert_text((60,140),'The stacks should not be')
 page.insert_text((60,165),'too high.')
 page.insert_text((60,200),'Suitable barriers should protect workers from an open edge and unsafe access routes.')
 page.insert_text((60,235),'Inspect equipment and ensure that damaged components are replaced before work starts.')
 passages,notes=chunking.extract(pdf.tobytes(),spec)
 text=' '.join(p.text for p in passages)
 assert 'too high.' in text and 'The stacks should not be' in text
 assert any(p.section=='4.1' and p.page_number==spec.index_page_start for p in passages)
 pdf.close()

def test_scanned_pdf_fails_clearly():
 pdf=pymupdf.open();pdf.new_page()
 with pytest.raises(KnowledgeError,match='native English text'):
  chunking.extract(pdf.tobytes(),source_set()[0])
 pdf.close()

def test_known_amended_section_not_retrievable():
 spec=next(s for s in source_set() if s.key=='metal')
 pdf=pymupdf.open()
 for _ in range(spec.index_page_start):pdf.new_page()
 page=pdf[-1]
 page.insert_text((60,70),'5.1.4 Working platforms')
 for y in range(110,300,35):page.insert_text((60,y),'Scaffolds should have working platforms and suitable guardrails to protect workers.')
 passages,_=chunking.extract(pdf.tobytes(),spec)
 assert passages and not any(p.active for p in passages)
 pdf.close()


def test_unreviewed_pdf_checksum_cannot_be_verified(indexed,db_factory):
 with db_factory() as db:
  with pytest.raises(KnowledgeError,match='reviewed checksum'):
   ingest.ingest_document(db,source_set()[0],b'%PDF-unreviewed-changed-content',utcnow(),indexed)
