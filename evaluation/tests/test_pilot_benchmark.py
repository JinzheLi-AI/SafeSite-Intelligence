"""Offline metric regression fixtures; no credentials, network, or real labels."""
import copy
import json
import pytest
from evaluation.report_vision_pilot import score, errors, generate
from evaluation.run_vision_pilot import write_json

def row(identifier, truth, prediction, review=False, expected=False):
    return dict(case_id=identifier, ground_truth_hazards=truth, predicted_hazards=prediction,
                provider_success=prediction is not None, requests_attempted=1,
                provider_error=None if prediction is not None else 'connection_error',
                expected_human_review=expected, ambiguous=expected, requires_human_review=review,
                hazard_confidences=[dict(hazard_type=h, confidence=.8) for h in prediction or []],
                latency_ms=100, input_tokens=10, output_tokens=20, total_tokens=30, estimated_cost_usd=None)

def run(rows):
    return dict(cases=rows, manifest_snapshot=copy.deepcopy(rows), status='completed')

def test_multilabel_counts_and_safe_review_separation():
    m=score(run([row('a',['missing_ppe','working_at_height'],['missing_ppe'],True,True),
                 row('b',[],['housekeeping'],True),row('c',['working_at_height'],['working_at_height'])]))
    assert m['micro']['precision']==pytest.approx(2/3)
    assert m['micro']['recall']==pytest.approx(2/3)
    assert m['micro']['f1']==pytest.approx(2/3)
    assert m['exact_match_rate']==pytest.approx(1/3)
    assert m['multi_hazard_exact_match_rate']==0
    assert m['safe_scene']['false_positive_rate']==1
    assert m['human_review']['ambiguous_case_review_recall']==1
    assert m['human_review']['unnecessary_review_rate']==.5
    assert m['per_class']['electrical_hazard']['f1'] is None
    assert m['total_tokens']==90
    assert m['estimated_cost_usd'] is None

def test_failures_never_become_safe_predictions():
    r=row('a',[],None)
    for k in ['input_tokens','output_tokens','total_tokens']:r[k]=None
    m=score(run([r]))
    assert m['successful_calls']==0 and m['failed_calls']==1
    assert m['exact_match_rate'] is None and m['micro']['f1'] is None
    assert m['safe_scene']['false_positive_rate'] is None
    assert m['total_tokens'] is None
    assert errors(run([r]))[0]['false_negative_classes'] is None

def test_unattempted_not_counted_as_failed_request():
    r=row('a',['missing_ppe'],None);r['requests_attempted']=0;r['provider_error']='not_attempted_after_stop'
    m=score(run([r]))
    assert m['failed_calls']==0 and m['unattempted_cases']==1
    assert m['per_class']['missing_ppe']['dataset_support']==1
    assert m['per_class']['missing_ppe']['support']==0

def test_empty_safe_prediction_is_exact_not_division_by_zero():
    m=score(run([row('a',[],[])]))
    assert m['exact_match_rate']==1 and m['safe_scene']['false_positive_rate']==0
    assert m['micro']['f1'] is None
    json.dumps(m,allow_nan=False)

def test_every_disagreement_retained():
    e=errors(run([row('a',['missing_ppe'],['working_at_height']),row('b',[],[])]))
    assert len(e)==1
    assert e[0]['false_positive_classes']==['working_at_height']
    assert e[0]['false_negative_classes']==['missing_ppe']

def test_atomic_cache_preserves_old_file_on_replace_failure(tmp_path,monkeypatch):
    path=tmp_path/'raw.json';path.write_text('{"old": true}')
    def fail(*args):raise OSError('interrupted')
    monkeypatch.setattr('evaluation.run_vision_pilot.os.replace',fail)
    with pytest.raises(OSError):write_json(path,{'new':True})
    assert json.loads(path.read_text())=={'old':True}
