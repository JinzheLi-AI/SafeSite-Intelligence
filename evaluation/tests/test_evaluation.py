import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from evaluation.schema import HazardCase,Prediction,RagCase,load,PENDING,VERIFIED,MOCKED
from evaluation.metrics import hazards,retrieval,workflow
from evaluation.runners.risk import run as risk_run
from evaluation.runners.workflow import score
from evaluation.runners.vision import run as vision_run
from evaluation.report import write

ROOT=Path(__file__).resolve().parents[1]
def case(id,labels,**kw):return HazardCase(case_id=id,description='fixture',ground_truth_hazards=labels,**kw)
def prediction(id,labels,**kw):return Prediction(case_id=id,hazards=labels,requires_human_review=True,**kw)
def query(id='q',expected=True):return RagCase(query_id=id,hazard_type='missing_ppe',query='helmet',should_return_evidence=expected,expected_source_families=['helmet'] if expected else [])
def citation(family='helmet',valid=True,verified=True):return dict(document_key=family,family=family,section='1.1',excerpt='helmet',stored_source_valid=valid,verified=verified)

def test_multilabel_hand_calculated():
    m=hazards([case('a',['missing_ppe','working_at_height']),case('b',[])],[prediction('a',['missing_ppe','housekeeping']),prediction('b',['electrical_hazard'])])
    assert m['micro']['tp']==1 and m['micro']['fp']==2 and m['micro']['fn']==1 and m['micro']['tn']==8
    assert m['precision']==pytest.approx(1/3) and m['recall']==.5 and m['micro_f1']==.4
    assert m['macro_f1']==.25 and m['exact_match_rate']==0
    assert m['micro']['false_positive_rate']==.2 and m['micro']['false_negative_rate']==.5

def test_empty_metrics_are_null():
    assert hazards([],[])['micro_f1'] is None
    assert retrieval([],[])['no_answer_accuracy'] is None
    assert workflow([])['workflow_success_rate'] is None
    assert risk_run([])['metrics']['classification_accuracy'] is None

@pytest.mark.parametrize('predictions',[[],[prediction('wrong',[])],[prediction('a',[]),prediction('a',[])]])
def test_cannot_drop_or_duplicate_predictions(predictions):
    with pytest.raises(ValueError):hazards([case('a',[])],predictions)

def test_placeholder_is_not_empty_truth():
    with pytest.raises(ValueError):hazards([case('a',None)],[prediction('a',[])])

def test_failed_call_is_not_successful_empty_scene():
    m=hazards([case('a',[])],[prediction('a',[],error='timeout')])
    assert m['errors']==1 and m['exact_match_rate']==0 and m['completion_rate']==0

def test_review_is_not_uncertainty():
    rows=[case('a',['missing_ppe'],ambiguous=True,expected_human_review=True),case('b',['missing_ppe'],ambiguous=False,expected_human_review=True)]
    m=hazards(rows,[prediction('a',['missing_ppe'],uncertain=True),prediction('b',['missing_ppe'],uncertain=False)])
    assert m['review_agreement']==1 and m['ambiguous_review_rate']==1 and m['obvious_uncertainty_rate']==0

def test_undefined_macro_classes_excluded():
    m=hazards([case('a',['missing_ppe'])],[prediction('a',['missing_ppe'])])
    assert m['macro_f1']==1 and m['per_class']['housekeeping']['f1'] is None

def test_rag_ranking_and_duplicates():
    q=query();q.expected_source_families=['helmet','height']
    m=retrieval([q],[dict(query_id='q',citations=[citation('other'),citation(),citation()])])
    assert m['recall_at_1']==0 and m['recall_at_3']==.5 and m['mrr']==.5
    assert m['precision_at_3']==pytest.approx(2/3)

def test_no_answer_and_infrastructure_failures():
    rows=[dict(query_id='a',citations=[]),dict(query_id='b',citations=[],error='index_unavailable'),dict(query_id='c',citations=[citation()])]
    m=retrieval([query(x,False) for x in ['a','b','c']],rows)
    assert m['no_answer_accuracy']==pytest.approx(1/3) and m['errors']==1
    assert m['recall_at_3'] is None

def test_unsupported_citation_rate_is_grounding_not_relevance():
    m=retrieval([query()],[dict(query_id='q',citations=[citation('irrelevant'),citation(valid=False,verified=False)])])
    assert m['unsupported_citation_rate']==.5 and m['verified_source_rate']==.5

def test_empty_citations_never_claim_zero_unsupported_rate():
    assert retrieval([query('a',False)],[dict(query_id='a',citations=[])])['unsupported_citation_rate'] is None

def test_section_judgments_enforced():
    q=query();q.expected_section_keywords=['chin strap']
    assert retrieval([q],[dict(query_id='q',citations=[citation()])])['mrr']==0

@pytest.mark.parametrize('bad',[dict(hazard_type='new_hazard'),dict(expected_source_families=[]),dict(extra='field')])
def test_rag_schema_validates(bad):
    with pytest.raises(ValidationError):RagCase.model_validate(query().model_dump()|bad)

def test_reviewed_images_require_provenance():
    with pytest.raises(ValidationError):HazardCase(case_id='a',description='fake',label_status='reviewed',ground_truth_hazards=[])

def test_manifest_duplicate_ids_rejected(tmp_path):
    p=tmp_path/'cases.json';p.write_text(json.dumps([case('a',[]).model_dump()]*2))
    with pytest.raises(ValueError):load(p,HazardCase)

def test_risk_dataset_independent_expected_outputs():
    cases=json.loads((ROOT/'datasets/risk.json').read_text())
    a=risk_run(cases);b=risk_run(cases)
    assert a==b and len(a['rows'])==40 and all(r['passed'] for r in a['rows'])
    corrupt=copy.deepcopy(cases);corrupt[0]['expected_level']='CRITICAL'
    assert not risk_run(corrupt)['rows'][0]['passed']

def test_workflow_subset_denominators_and_missing_results():
    cases=[{'node':'a','case_id':'a','criteria':['human_control']},{'node':'b','case_id':'b','criteria':['audit_completeness']}]
    m=score(cases,{'a':{'passed':True}})['metrics']
    assert m['workflow_success_rate']==.5 and m['human_control']['success_rate']==1 and m['audit_completeness']['success_rate']==0
    assert m['state_transition']['success_rate'] is None

def test_vision_pending_without_images_even_if_live_requested(tmp_path,monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'openai_api_key',None)
    result=vision_run([case('placeholder',None)],tmp_path,tmp_path,live=True)
    assert result['status']==PENDING and result['baselines']=={}

def test_report_has_separate_statuses_and_no_joint_score(tmp_path):
    summary={'hazard':{'status':PENDING,'baselines':{}},'retrieval':{'status':VERIFIED,'baselines':{}},
             'risk':risk_run([]),'workflow':score([], {})}
    write(summary,tmp_path)
    saved=json.loads((tmp_path/'summary.json').read_text())
    assert saved['hazard']['status']==PENDING and saved['workflow']['status']==MOCKED
    assert all(x['joint_score'] is None for x in saved['ablations'])
    assert 'Pending live evaluation' in (tmp_path/'summary.md').read_text()
    assert (tmp_path/'risk.json').exists()

def test_all_manifest_counts_and_workflow_node_uniqueness():
    assert len(load(ROOT/'datasets/hazards.json',HazardCase))==72
    assert len(load(ROOT/'datasets/retrieval.json',RagCase))==48
    rows=json.loads((ROOT/'datasets/workflow.json').read_text())
    assert len(rows)==len({r['node'] for r in rows})==20

def test_paired_vision_adapter_uses_same_images_and_restores_settings(tmp_path,monkeypatch):
    import hashlib
    from pydantic import SecretStr
    from app.core.config import settings
    from app.ai.vision_contracts import VisualInspectionOutput
    from evaluation.runners import vision
    raw=VisualInspectionOutput(summary='Injected fixture',hazards=[],overall_confidence=.95,requires_human_review=False,ambiguity_detected=False,reasoning_notes=[])
    image=tmp_path/'image.jpg';image.write_bytes(b'unit-test-only-image-bytes')
    c=case('a',[],label_status='reviewed',image_path='image.jpg',image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),group_id='same-site',reviewers=['reviewer-a','reviewer-b'],license_or_consent='test fixture',ambiguous=False,expected_human_review=False)
    calls=[]
    class Stub:
        model_name='injected-test-model'
        prompt_hash='test'
        def _request(self,*args):calls.append('generic');self.raw=raw;return raw
        def analyze_inspection(self,**kwargs):calls.append('safesite');self.raw=raw;return raw
    monkeypatch.setattr(vision,'RecordingProvider',Stub)
    monkeypatch.setattr(vision,'image_data_url',lambda value:'data:image/jpeg;base64,fixture')
    monkeypatch.setattr(settings,'openai_api_key',SecretStr('offline-test'))
    original=settings.upload_dir
    r=vision.run([c],tmp_path,tmp_path,live=True)
    assert calls==['generic','safesite'] and settings.upload_dir==original
    assert set(r['baselines'])=={'generic_direct','safesite'}
    assert all(x['metrics']['exact_match_rate']==1 for x in r['baselines'].values())
    image.write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):vision.run([c],tmp_path,tmp_path,live=True)


@pytest.mark.parametrize('model_id',['openai/gpt-5.6-terra','openai/gpt-5.6-sol','deepseek/deepseek-flash'])
def test_evaluation_model_dimension_pending_without_calls(tmp_path,model_id):
    from evaluation.runners import vision
    result=vision.run([],tmp_path,tmp_path,model_id=model_id)
    assert result['model_id']==model_id
    assert result['provider']+'/'+result['model']==model_id
    assert result['baselines']=={}


def test_evaluation_rejects_text_only_vision_model(tmp_path):
    from evaluation.runners import vision
    from app.ai.errors import AIProviderError
    with pytest.raises(AIProviderError):vision.run([],tmp_path,tmp_path,model_id='deepseek/deepseek-v4-pro')


@pytest.mark.parametrize('model_id',['openai/gpt-5.6-sol','deepseek/deepseek-flash'])
def test_model_case_records_include_actual_usage(tmp_path,monkeypatch,model_id):
    import hashlib
    from pydantic import SecretStr
    from app.core.config import settings
    from app.ai.vision_contracts import VisualInspectionOutput
    from evaluation.runners import vision
    raw=VisualInspectionOutput(summary='Fixture',hazards=[],overall_confidence=.95,requires_human_review=False,ambiguity_detected=False,reasoning_notes=[])
    image=tmp_path/'image.jpg';image.write_bytes(b'fixture')
    c=case('same-case',[],label_status='reviewed',image_path='image.jpg',image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),group_id='site',reviewers=['a','b'],license_or_consent='fixture',ambiguous=False,expected_human_review=False)
    class Stub:
        prompt_version='vision-test';prompt_hash='fixture'
        def __init__(self,config):
            self.model_name=config.vision_model
            self.call_records=[dict(input_tokens=111,output_tokens=22,total_tokens=133,estimated_cost_usd=None)]
        def _request(self,*args):self.raw=raw;return raw
        def analyze_inspection(self,**kw):self.raw=raw;return raw
    monkeypatch.setattr(vision,'RecordingProvider',Stub)
    monkeypatch.setattr(vision,'RecordingDeepSeekProvider',Stub)
    monkeypatch.setattr(vision,'image_data_url',lambda path:'fixture')
    monkeypatch.setattr(settings,'openai_api_key',SecretStr('fixture'))
    monkeypatch.setattr(settings,'deepseek_api_key',SecretStr('fixture'))
    result=vision.run([c],tmp_path,tmp_path,live=True,model_id=model_id,validation_attempts=1)
    rows=json.loads((tmp_path/'vision-calls.json').read_text())
    assert result['max_validation_attempts']==1 and len(rows)==2
    for row in rows:
        assert row['model_id']==model_id and row['case_id']=='same-case'
        assert row['input_tokens']==111 and row['total_tokens']==133
        assert row['estimated_cost_usd'] is None and row['prompt_version']==('evaluation-generic-v1' if row['baseline']=='generic_direct' else 'vision-test')


def test_evaluation_inherits_real_vision_provider(tmp_path,monkeypatch):
    from app.core.config import settings
    from evaluation.runners import vision
    monkeypatch.setattr(settings,'vision_provider','deepseek')
    monkeypatch.setattr(settings,'vision_model','deepseek-flash')
    assert vision.run([],tmp_path,tmp_path)['model_id']=='deepseek/deepseek-flash'
