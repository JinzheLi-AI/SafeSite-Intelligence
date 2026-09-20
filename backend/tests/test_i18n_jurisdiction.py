import re
import pytest
from sqlalchemy import create_engine, text
from app.core.localization import dictionary, tr
from app.core.jurisdictions import ensure_project_jurisdiction, project_context
from app.analyst.service import SafetyAnalystService
from app.ai.mock import MockSafetyAIProvider
from app.knowledge.retrieval import search
from app.models.entities import Project
from test_analyst import population, NOW
from test_knowledge import indexed, TEXT

QUESTIONS=[k for k in dictionary('zh-CN') if k.startswith(('What ','Which ','Show ','Compare ','How '))]

def test_locale_parity_and_domain_coverage():
    en,zh=dictionary('en'),dictionary('zh-CN')
    assert en.keys()==zh.keys()
    assert all(isinstance(v,str) and v.strip() for v in zh.values())
    for key in ['working_at_height','missing_ppe','unprotected_edge','unsafe_scaffolding','electrical_hazard','housekeeping','LOW','MEDIUM','HIGH','CRITICAL','OPEN','UNDER_REVIEW','RECTIFICATION','REINSPECTION','CLOSED','REJECTED','PENDING','CONFIRMED','MODIFIED']:
        assert re.search('[\u4e00-\u9fff]',zh[key])
    assert zh['CRITICAL']=='\u4e25\u91cd\u98ce\u9669'
    assert zh['working_at_height']=='\u9ad8\u5904\u4f5c\u4e1a'

@pytest.mark.parametrize('question',QUESTIONS)
def test_bilingual_metrics_share_sql_and_rows(population,question):
    service=SafetyAnalystService(population,now=NOW)
    en=service.ask(question,language='en')
    zh=service.ask(tr(question,'zh-CN'),language='zh-CN')
    assert en.status==zh.status=='success'
    assert en.metric==zh.metric
    assert en.rows==zh.rows
    assert en.sql==zh.sql
    assert en.chart==zh.chart
    assert re.search('[\u4e00-\u9fff]',zh.answer)
    assert zh.localized['en']['answer']==en.answer
    assert zh.metric_definition!=en.metric_definition

@pytest.mark.parametrize('code',['CN','SG','MY','unknown',None])
def test_no_cross_jurisdiction_fallback(indexed,db_factory,code):
    with db_factory() as db:
        result=search(db,'working_at_height',TEXT['working_at_height'],embedder=indexed,jurisdiction=code)
        assert result.status=='unavailable' and not result.citations
        assert result.candidate_count==0

def test_hk_retrieval_preserves_original(indexed,db_factory):
    with db_factory() as db:
        result=search(db,'working_at_height',TEXT['working_at_height'],embedder=indexed,jurisdiction=project_context(db,1)['regulatory_jurisdiction'])
        assert result.status=='success' and result.citations
        assert all(c.jurisdiction=='Hong Kong' and c.verified and c.active for c in result.citations)
        assert all(c.excerpt in TEXT.values() for c in result.citations)

def test_context_and_api_fail_closed(client,db_factory,indexed):
    assert client.get('/api/v1/knowledge/context').json()['regulatory_jurisdiction']=='HK-SAR'
    with db_factory() as db:
        db.get(Project,1).regulatory_jurisdiction='CN';db.commit()
    context=client.get('/api/v1/knowledge/context?project_id=1').json()
    assert not context['supported']
    assert [x['code'] for x in context['options'] if x['supported']]==['HK-SAR']
    docs=client.get('/api/v1/knowledge/documents?project_id=1').json()
    assert not any(x.get('verified') for x in docs)
    for project_id in [1,999]:
        result=client.post('/api/v1/knowledge/search',json={'project_id':project_id,'hazard_type':'working_at_height','query':'fall prevention'}).json()
        assert result['status']=='unavailable' and result['citations']==[]

def test_existing_project_upgrade_preserves_records(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'legacy.db'))
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT)'))
        conn.execute(text("INSERT INTO projects VALUES (1, 'Existing project')"))
    ensure_project_jurisdiction(engine);ensure_project_jurisdiction(engine)
    with engine.connect() as conn:
        assert tuple(conn.execute(text('SELECT * FROM projects')).one())==(1,'Existing project','HK-SAR')
    engine.dispose()

def test_mock_language_preserves_machine_fields():
    provider=MockSafetyAIProvider()
    en=provider.analyze_inspection(location='L2',description=None,image_path=None)
    provider.output_language='zh-CN'
    zh=provider.analyze_inspection(location='L2',description=None,image_path=None)
    assert en.summary!=zh.summary
    for a,b in zip(en.hazards,zh.hazards):
        assert a.hazard_type==b.hazard_type and a.risk_score==b.risk_score and a.risk_level==b.risk_level
        assert a.regulation_queries==b.regulation_queries
        assert re.search('[\u4e00-\u9fff]',b.description)
        assert a.visual_evidence!=b.visual_evidence and a.recommended_actions!=b.recommended_actions
    result=provider.analyze_reinspection(incident_id=1,previous_risk=85,evidence_path=None,notes='')
    assert result.current_risk_score==15 and result.recommendation=='ELIGIBLE_FOR_CLOSURE'
    assert all(re.search('[\u4e00-\u9fff]',e) for e in result.evidence)
from test_real_provider import provider, observation, hazard, saved_image, analyze

def test_real_language_prompt_keeps_contract(saved_image):
    instance=provider(observation([hazard(description='\u4e34\u8fb9\u4f5c\u4e1a\u98ce\u9669')]))
    instance.output_language='zh-CN'
    result=analyze(instance,saved_image)
    request=str(instance._injected_client.responses.parse.call_args.kwargs)
    assert 'zh-CN' in request and 'regulation_queries' in request
    assert result.hazards[0].hazard_type=='working_at_height'
    assert result.hazards[0].risk_score==85 and result.requires_human_review
    assert result.hazards[0].description=='\u4e34\u8fb9\u4f5c\u4e1a\u98ce\u9669'

def test_language_header_and_validation(client):
    body={'project_id':1,'site_id':1,'location_text':'L2','source_type':'DEMO'}
    created=client.post('/api/v1/inspections',json=body).json()
    path='/api/v1/inspections/'+str(created['id'])+'/analyze'
    assert client.post(path,headers={'X-SafeSite-Language':'invalid'}).status_code==422
    result=client.post(path,headers={'X-SafeSite-Language':'zh-CN'}).json()
    assert result['analysis_source']['output_language']=='zh-CN'
    assert result['hazards'][0]['hazard_type']=='working_at_height'
    assert re.search('[\u4e00-\u9fff]',result['hazards'][0]['description'])
    assert client.post('/api/v1/analyst/query',json={'question':'test','language':'invalid'}).status_code==422
