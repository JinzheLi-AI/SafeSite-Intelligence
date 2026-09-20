import copy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import pytest
from PIL import Image
from evaluation.label_vision_dataset import read_manifest, save_review, make_handler


@pytest.fixture
def document(tmp_path):
    image=tmp_path/'fixture.png';Image.new('RGB',(12,8),'gray').save(image)
    rows=[]
    for i in range(20):
        rows.append(dict(case_id=f'case_{i+1:03d}',image_path=None,image_hash=None,
            ground_truth_hazards=None,ambiguous=None,expected_human_review=None,
            evidence_notes=None,reviewer=None,secondary_reviewer=None,label_status='missing_image',
            source=None,license_or_provenance=None,group=None))
    rows[0].update(image_path=image.name,image_hash=hashlib.sha256(image.read_bytes()).hexdigest(),label_status='unreviewed')
    path=tmp_path/'manifest.json';path.write_text(json.dumps(rows),encoding='utf-8')
    fields=dict(ground_truth_hazards=[],ambiguous=False,expected_human_review=False,
        evidence_notes='Human-authored test fixture note.',reviewer='Test reviewer',secondary_reviewer=None,
        source='',license_or_provenance='',group=None)
    return path, fields


def save(document):
    path,fields=document
    return save_review(path,'case_001',fields,read_manifest(path)[1],path.parent)


def test_save_safe_review_preserves_every_other_case_and_image_identity(document):
    path,fields=document;before,_=read_manifest(path)
    result=save(document);after,_=read_manifest(path)
    assert result['benchmark_ready']==1 and after[0]['label_status']=='reviewed'
    assert after[0]['ground_truth_hazards']==[] and after[0]['secondary_reviewer'] is None
    assert after[1:]==before[1:]
    for field in ['case_id','image_path','image_hash']:assert after[0][field]==before[0][field]
    assert not list(path.parent.glob('.label-review-*')) and not Path(str(path)+'.labeling.lock').exists()


@pytest.mark.parametrize('field,value',[
    ('reviewer','  '),('evidence_notes',''),('ambiguous',None),('expected_human_review',None),
    ('ambiguous','false'),('ground_truth_hazards',['unsupported']),('ground_truth_hazards',None)])
def test_invalid_save_leaves_file_byte_identical(document,field,value):
    path,fields=document;before=path.read_bytes();fields[field]=value
    with pytest.raises(ValueError):save(document)
    assert path.read_bytes()==before


def test_group_does_not_change_hazards(document):
    path,fields=document;fields['group']='ppe'
    save(document)
    assert read_manifest(path)[0][0]['ground_truth_hazards']==[]


def test_protected_field_rejected(document):
    path,fields=document;before=path.read_bytes();fields['image_path']='different.jpg'
    with pytest.raises(ValueError):save(document)
    assert path.read_bytes()==before


def test_stale_page_does_not_overwrite_other_edits(document):
    path,fields=document;rows,revision=read_manifest(path);rows[1]['source']='Human edit elsewhere'
    path.write_text(json.dumps(rows),encoding='utf-8');before=path.read_bytes()
    with pytest.raises(ValueError,match='changed since'):
        save_review(path,'case_001',fields,revision,path.parent)
    assert path.read_bytes()==before


def test_atomic_replace_failure_leaves_valid_original(document,monkeypatch):
    from evaluation import label_vision_dataset as module
    path,_=document;before=path.read_bytes()
    def fail(*args):raise OSError('Simulated interruption before replacement')
    monkeypatch.setattr(module.os,'replace',fail)
    with pytest.raises(OSError):save(document)
    assert path.read_bytes()==before and len(json.loads(path.read_text()))==20
    assert not list(path.parent.glob('.label-review-*'))


def test_active_save_lock_blocks_overwrite(document):
    path,_=document;lock=Path(str(path)+'.labeling.lock');lock.write_text('')
    before=path.read_bytes()
    with pytest.raises(ValueError,match='Another save'):save(document)
    assert path.read_bytes()==before and lock.exists()


def test_loopback_http_read_validate_and_save_protection(document):
    from http.server import ThreadingHTTPServer
    from http.client import HTTPConnection
    from threading import Thread
    path,fields=document;before=path.read_bytes()
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(path,path.parent,token='fixture-token'))
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
    try:
        conn.request('GET','/dataset');response=conn.getresponse();data=json.loads(response.read())
        assert response.status==200 and len(data['cases'])==20
        conn.request('POST','/save',body=json.dumps({'case_id':'case_001','fields':fields,'revision':data['revision']}),headers={'Content-Type':'application/json'})
        response=conn.getresponse();response.read();assert response.status==403 and path.read_bytes()==before
        conn.request('POST','/validate',body='{}',headers={'X-Label-Token':'fixture-token'})
        response=conn.getresponse();validation=json.loads(response.read())
        assert response.status==200 and validation['benchmark_ready']==0
        conn.request('GET','/image/case_001');response=conn.getresponse()
        assert response.status==200 and response.read()==(path.parent/'fixture.png').read_bytes()
    finally:
        conn.close();server.shutdown();server.server_close();worker.join()
