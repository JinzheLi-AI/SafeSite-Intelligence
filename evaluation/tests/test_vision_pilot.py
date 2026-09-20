import hashlib
import json
import pytest
from evaluation.validate_vision_dataset import validate_dataset


@pytest.fixture
def pilot(tmp_path):
    # File-content identity tests need no model or product settings.
    image=tmp_path/'photo.jpg';image.write_bytes(b'image-content-fixture')
    rows=[]
    for i in range(20):
        rows.append(dict(case_id=f'case_{i+1:03d}',image_path=None,image_hash=None,
            ground_truth_hazards=None,ambiguous=None,expected_human_review=None,
            evidence_notes=None,reviewer=None,secondary_reviewer=None,label_status='missing_image',
            source=None,license_or_provenance=None,group=None))
    rows[0].update(image_path='photo.jpg',image_hash=hashlib.sha256(image.read_bytes()).hexdigest(),label_status='unreviewed')
    def check():
        manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(rows),encoding='utf-8')
        return validate_dataset(manifest,tmp_path)
    return rows,check


def reviewed(row,**changes):
    row.update(label_status='reviewed',reviewer='Human A',evidence_notes='Human test annotation only.',
        ground_truth_hazards=[],ambiguous=False,expected_human_review=False,**changes)


def test_safe_reviewed_case_and_optional_secondary(pilot):
    rows,check=pilot;reviewed(rows[0])
    r=check()
    assert r['errors']==[] and r['benchmark_ready']==1 and r['ready_case_ids']==['case_001']
    assert rows[0]['secondary_reviewer'] is None


@pytest.mark.parametrize('field,value',[
    ('ground_truth_hazards',['new_category']),('reviewer','  '),('evidence_notes',None),
    ('ambiguous','false'),('expected_human_review',1),('ground_truth_hazards',None),
    ('ground_truth_hazards',['missing_ppe','missing_ppe'])])
def test_invalid_reviewed_fields(pilot,field,value):
    rows,check=pilot;reviewed(rows[0]);rows[0][field]=value
    r=check();assert r['errors'] and r['benchmark_ready']==0


def test_missing_slots_accepted_and_unreviewed_not_ready(pilot):
    _,check=pilot;r=check()
    assert r['total_cases']==20 and r['images_present']==1 and r['missing_images']==19
    assert not r['errors'] and r['benchmark_ready']==0


def test_duplicates_exclude_both_even_with_mismatched_claim(pilot):
    rows,check=pilot;reviewed(rows[0]);rows[1]=dict(rows[0],case_id='case_002',image_hash='0'*64)
    r=check();assert r['duplicate_images']==1 and r['benchmark_ready']==0
    assert any('Duplicate image hash' in x for x in r['errors'])


def test_hash_mismatch(pilot):
    rows,check=pilot;reviewed(rows[0]);rows[0]['image_hash']='0'*64
    r=check();assert any('hash mismatch' in x for x in r['errors']) and r['benchmark_ready']==0


def test_secondary_optional_for_adjudicated(pilot):
    rows,check=pilot;reviewed(rows[0]);rows[0]['label_status']='adjudicated'
    r=check();assert not r['errors'] and r['adjudicated']==1 and r['benchmark_ready']==1


@pytest.mark.parametrize('change',['count','duplicate_id','wrong_id','missing_file','traversal','bad_group'])
def test_structure_and_path_errors(pilot,change):
    rows,check=pilot
    if change=='count':rows.pop()
    elif change=='duplicate_id':rows[1]['case_id']='case_001'
    elif change=='wrong_id':rows[1]['case_id']='case_099'
    elif change=='missing_file':rows[0]['image_path']='absent.jpg'
    elif change=='traversal':rows[0]['image_path']='../photo.jpg'
    else:rows[0]['group']='invented'
    assert check()['errors']


def test_missing_image_cannot_claim_negative_label(pilot):
    rows,check=pilot;rows[1]['ground_truth_hazards']=[]
    assert check()['errors']


def test_invalid_hazard_in_unreviewed_case(pilot):
    rows,check=pilot;rows[0]['ground_truth_hazards']=['not_supported']
    assert check()['errors']


def test_manifest_invalid_json(tmp_path):
    p=tmp_path/'bad.json';p.write_text('{')
    assert validate_dataset(p,tmp_path)['errors']
