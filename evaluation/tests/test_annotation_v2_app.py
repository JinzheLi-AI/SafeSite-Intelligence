"""Real local HTTP handlers + generated images; temporary datasets only, no inference."""
import base64
import copy
import json
from io import BytesIO
from pathlib import Path
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
import pytest
from PIL import Image
from evaluation.label_vision_dataset import make_handler
from evaluation.annotation_store import HAZARDS,freeze_hash

@pytest.fixture
def local_app(tmp_path):
    source=Path(__file__).resolve().parents[1]/'datasets'
    paths={}
    for key,name in [('development','development'),('heldout','heldout')]:
        doc=json.loads((source/f'vision_v2_{name}_v1.json').read_text(encoding='utf-8'))
        doc['cases']=doc['cases'][:2];doc['target_image_count']=2
        # Tests must not inherit user annotations or imported paths from live data.
        for row in doc['cases']:
            for field in list(row):
                if field != 'case_id':row[field]=None
            row.update(class_decisions={h:None for h in HAZARDS},review_status='unreviewed',
                       site_identity_status='unknown',scene_identity_status='unknown',related_image_review_status='pending')
        doc.update(freeze_status='not_ready',frozen_at=None,frozen_manifest_sha256=None)
        p=tmp_path/(key+'.json');p.write_text(json.dumps(doc));paths[key]=p
    p=tmp_path/'historical.json';p.write_text('[]');paths['historical']=p
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(image_root=tmp_path,datasets=paths,token='local-test-token'))
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    def request(method,route,data=None,token='local-test-token'):
        conn=HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        try:
            conn.request(method,route,body=json.dumps(data) if data is not None else None,headers={'X-Label-Token':token,'Content-Type':'application/json'})
            response=conn.getresponse();body=response.read()
            return response.status,json.loads(body) if 'json' in response.getheader('Content-Type','') else body
        finally:conn.close()
    yield request,paths,tmp_path
    server.shutdown();server.server_close();worker.join()

def picture(color='blue',fmt='PNG'):
    b=BytesIO();Image.new('RGB',(24,16),color).save(b,format=fmt);return base64.b64encode(b.getvalue()).decode()

def load(request,key):
    status,d=request('GET','/dataset?dataset='+key);assert status==200;return d

def upload(request,key,cid,color='blue',fmt='PNG'):
    d=load(request,key)
    return request('POST','/import?dataset='+key,dict(case_id=cid,revision=d['revision'],image_base64=picture(color,fmt)))

def annotation():
    return dict(class_decisions={h:'negative' for h in HAZARDS},ambiguous=False,expected_uncertainty_review=False,
        requires_safety_adjudication=False,operational_human_confirmation=False,evidence_notes='Synthetic test-only reviewer entry; not a real scene judgment.',reviewer='Offline test reviewer',review_status='reviewed',
        permission_verified=True,permission_evidence='Generated locally by this test.',license_or_provenance='Synthetic test fixture.',related_image_review_status='reviewed')

def test_full_import_annotate_validate_duplicate_freeze_acceptance(local_app):
    request,paths,root=local_app;original={k:p.read_bytes() for k,p in paths.items()}
    first='v2_heldout_001';second='v2_heldout_002'
    assert upload(request,'heldout',first)[0]==200
    d=load(request,'heldout');row=d['cases'][0]
    assert (root/row['image_path']).read_bytes()==base64.b64decode(picture())
    assert row['review_status']=='unreviewed' and row['ground_truth_hazards'] is None
    assert request('POST','/save?dataset=heldout',dict(case_id=first,fields=annotation(),revision=d['revision']))[0]==200
    d=load(request,'heldout');assert d['cases'][0]['ground_truth_hazards']==[] and d['cases'][0]['reviewer']=='Offline test reviewer'
    assert upload(request,'heldout',second)[0]==400
    # Across-split duplicates are rejected, too.
    assert upload(request,'development','v2_development_001')[0]==400
    assert upload(request,'heldout',second,'green','JPEG')[0]==200
    d=load(request,'heldout');assert request('POST','/save?dataset=heldout',dict(case_id=second,fields=annotation(),revision=d['revision']))[0]==200
    status,v=request('POST','/validate?dataset=heldout',{});assert status==200 and v['errors']==[] and v['benchmark_ready']==2
    d=load(request,'heldout');assert request('POST','/freeze?dataset=heldout',dict(revision=d['revision'],acknowledged=True))[0]==200
    frozen_bytes=paths['heldout'].read_bytes();doc=json.loads(frozen_bytes);assert doc['frozen_manifest_sha256']==freeze_hash(doc)
    d=load(request,'heldout');assert d['readonly']
    assert request('POST','/save?dataset=heldout',dict(case_id=first,fields=annotation(),revision=d['revision']))[0]==400
    assert upload(request,'heldout',first,'red')[0]==400
    assert paths['heldout'].read_bytes()==frozen_bytes
    assert paths['historical'].read_bytes()==original['historical'] and paths['development'].read_bytes()==original['development']

@pytest.mark.parametrize('bad',[base64.b64encode(b'not an image').decode(),'!!!'])
def test_invalid_image_and_csrf_cannot_mutate(local_app,bad):
    req,paths,root=local_app;before=paths['development'].read_bytes();d=load(req,'development')
    payload=dict(case_id='v2_development_001',revision=d['revision'],image_base64=bad)
    assert req('POST','/import?dataset=development',payload)[0]==400
    assert req('POST','/import?dataset=development',payload,token='wrong')[0]==403
    assert paths['development'].read_bytes()==before

def test_readonly_history_and_incomplete_freeze(local_app):
    req,paths,root=local_app;d=load(req,'historical');before=paths['historical'].read_bytes()
    assert d['readonly']
    assert req('POST','/save?dataset=historical',dict(case_id='x',fields=annotation(),revision=d['revision']))[0]==400
    assert req('POST','/import?dataset=historical',dict(case_id='x',image_base64=picture(),revision=d['revision']))[0]==400
    assert paths['historical'].read_bytes()==before
    d=load(req,'heldout');assert req('POST','/freeze?dataset=heldout',dict(revision=d['revision'],acknowledged=True))[0]==400

def test_invalid_annotation_stale_revision_and_indeterminate(local_app):
    req,paths,root=local_app;d=load(req,'development');stale=d['revision']
    assert upload(req,'development','v2_development_001')[0]==200
    assert req('POST','/save?dataset=development',dict(case_id='v2_development_001',fields=annotation(),revision=stale))[0]==400
    d=load(req,'development');before=paths['development'].read_bytes();a=annotation();a['class_decisions']['missing_ppe']='indeterminate'
    assert req('POST','/save?dataset=development',dict(case_id='v2_development_001',fields=a,revision=d['revision']))[0]==400
    assert paths['development'].read_bytes()==before
    a.update(ambiguous=True,expected_uncertainty_review=True,requires_safety_adjudication=True)
    assert req('POST','/save?dataset=development',dict(case_id='v2_development_001',fields=a,revision=d['revision']))[0]==200
    d=load(req,'development');assert d['cases'][0]['class_decisions']['missing_ppe']=='indeterminate' and d['cases'][0]['ground_truth_hazards']==[]

def test_group_leakage_blocks_freeze(local_app):
    req,paths,root=local_app
    for key,color in [('development','red'),('heldout','blue')]:
        upload(req,key,f'v2_{key}_001',color)
        d=load(req,key);a=annotation();a.update(source_site_id='human-supplied-site-A',site_identity_status='known')
        assert req('POST','/save?dataset='+key,dict(case_id=f'v2_{key}_001',fields=a,revision=d['revision']))[0]==(200 if key=='development' else 400)
    assert load(req,'heldout')['cases'][0]['source_site_id'] is None


def test_development_readiness_reports_only_actual_blocker(local_app):
    req,paths,root=local_app
    assert upload(req,'development','v2_development_001')[0]==200
    d=load(req,'development');a=annotation();a['related_image_review_status']='pending'
    assert req('POST','/save?dataset=development',dict(case_id='v2_development_001',fields=a,revision=d['revision']))[0]==200
    _,v=req('POST','/validate?dataset=development',{})
    message=next(w for w in v['warnings'] if 'blocked:' in w)
    assert 'related_image_review_status' in message and 'pending' in message
    assert 'permission' not in message and 'freeze' not in message
    assert v['benchmark_ready']==0
    d=load(req,'development')
    assert req('POST','/save?dataset=development',dict(case_id='v2_development_001',fields={'related_image_review_status':'reviewed'},revision=d['revision']))[0]==200
    _,v=req('POST','/validate?dataset=development',{})
    assert v['benchmark_ready']==1 and not v['frozen']
    assert any('site unknown' in w for w in v['warnings'])
