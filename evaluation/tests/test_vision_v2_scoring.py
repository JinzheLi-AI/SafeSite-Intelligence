import copy
import hashlib
import json
from pathlib import Path
import pytest
from evaluation.vision_v2_scoring import score, eligibility, HAZARDS, MANIFEST_SCHEMA
from evaluation.report_vision_pilot import score as legacy_score

ROOT=Path(__file__).resolve().parents[2]
def case(cid,positive=(),unknown=(),review=False):
    return dict(case_id=cid,ground_truth_hazards=list(positive),class_decisions={h:'positive' if h in positive else 'indeterminate' if h in unknown else 'negative' for h in HAZARDS},expected_uncertainty_review=review)
def doc(*rows):return dict(schema_version=MANIFEST_SCHEMA,cases=list(rows))
def pred(cid,labels=(),flag=None,success=True):
    return dict(case_id=cid,predicted_hazards=list(labels),model_uncertainty_review=flag,provider_success=success,requires_human_review=True,operational_human_confirmation=True)

def test_manual_three_case_arithmetic():
    d=doc(case('safe'),case('unknown',unknown=['housekeeping'],review=True),case('positive',positive=['missing_ppe']))
    m=score(d,[pred('safe',['housekeeping'],False),pred('unknown',['housekeeping'],True),pred('positive',['missing_ppe'],False)])
    # 18 pairs minus one unknown =17: TP1 FP1 FN0 TN15.
    assert [m['micro'][k] for k in ['tp','fp','fn','tn']]==[1,1,0,15]
    assert m['micro']['precision']==.5 and m['micro']['recall']==1
    assert m['micro']['f1']==pytest.approx(2/3)
    assert m['macro']==dict(precision=.5,recall=1,f1=.5)
    assert m['macro_defined_class_counts']==dict(precision=2,recall=1,f1=2)
    assert m['safe_scene']==dict(confirmed_count=1,correctly_predicted_count=0,false_positive_count=1,false_positive_rate=1,unknown_status_scene_count=1)
    assert m['full_exact_match']['evaluable_count']==2 and m['full_exact_match']['accuracy']==.5
    assert m['partial_known_label_agreement']['rate']==1
    assert m['per_class']['electrical_hazard']['positive_support']==0
    assert m['per_class']['electrical_hazard']['f1'] is None
    assert m['uncertainty_review']['correct_flags']==1 and m['uncertainty_review']['unnecessary_rate']==0
    assert m['case_errors'][1]['false_positive_classes']==[]

@pytest.mark.parametrize('prediction',[[],['housekeeping']])
def test_actual_case_008_mask_and_roundtrip(prediction):
    d=json.loads((ROOT/'evaluation/datasets/vision_v2_development_v1.json').read_text(encoding='utf-8'))
    r=next(r for r in d['cases'] if r['case_id']=='v2_development_008');original=copy.deepcopy(r)
    m=score(json.loads(json.dumps(doc(r))),[pred(r['case_id'],prediction)])
    h=m['per_class']['housekeeping']
    assert all(h[k]==0 for k in ['tp','fp','fn','tn','evaluable_sample_count'])
    assert h['indeterminate_count']==1 and sum(v['evaluable_sample_count'] for v in m['per_class'].values())==5
    assert m['safe_scene']['confirmed_count']==0 and m['safe_scene']['unknown_status_scene_count']==1
    assert m['full_exact_match']['evaluable_count']==0 and m['uncertainty_review']['status']=='unavailable'
    assert r==original

def test_safe_empty_and_missing_review_not_aggregate_mapping():
    m=score(doc(case('s')), [pred('s')])
    assert m['safe_scene']['correctly_predicted_count']==1
    assert m['full_exact_match']['accuracy']==1
    assert m['uncertainty_review']['unnecessary_rate'] is None
    assert m['uncertainty_review']['status']=='unavailable'

def test_failures_missing_predictions_and_explicit_schema():
    d=doc(case('s'))
    m=score(d,[pred('s',success=False)])
    assert m['coverage']==0 and m['safe_scene']['confirmed_count']==0 and m['micro']['f1'] is None
    with pytest.raises(ValueError):score(d,[])
    with pytest.raises(ValueError):eligibility(doc(dict(case_id='x',ground_truth_hazards=[])))
    with pytest.raises(ValueError):legacy_score(dict(manifest_snapshot=d['cases'],cases=[]))

def test_unknown_with_positive_and_partial_review_denominators():
    d=doc(case('a',['missing_ppe'],['housekeeping'],True),case('b',review=True),case('c'))
    m=score(d,[pred('a',['missing_ppe'],False),pred('b'),pred('c',flag=True)])
    assert m['safe_scene']['unknown_status_scene_count']==1
    assert m['uncertainty_review']['status']=='partial'
    assert m['uncertainty_review']['missed_flags']==1
    assert m['uncertainty_review']['unnecessary_rate']==1
    assert m['uncertainty_review']['evaluable_count']==2

def test_historical_frozen_evidence_unchanged():
    q=json.loads((ROOT/'evaluation/adjudication/vision_pilot_20_review_queue.json').read_text(encoding='utf-8'))
    for name,digest in q['frozen_files_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
