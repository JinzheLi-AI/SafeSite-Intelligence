"""Offline V2 annotation storage. No provider or production imports."""
import base64
import hashlib
import json
import os
import tempfile
import warnings
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image

HAZARDS = ['missing_ppe','working_at_height','unprotected_edge','unsafe_scaffolding','electrical_hazard','housekeeping']
MAX_IMAGE = 10 * 1024 * 1024
TEXT = ['source_url','source_platform','original_image_id','license_or_provenance','permission_evidence','source_site_id','source_scene_id','site_scene_group','evidence_notes','reviewer','secondary_reviewer','reviewer_prior_exposure']
FLAGS = ['ambiguous','expected_uncertainty_review','requires_safety_adjudication','operational_human_confirmation','permission_verified']
ENUMS = {'site_identity_status':['unknown','known'], 'scene_identity_status':['unknown','known'], 'related_image_review_status':['pending','reviewed'], 'review_status':['unreviewed','reviewed','adjudicated']}
EDITABLE = set(TEXT + FLAGS + list(ENUMS) + ['class_decisions'])

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path):
    data=Path(path).read_bytes()
    return json.loads(data.decode('utf-8-sig')),sha(data)

def atomic(path, data):
    path=Path(path);temp=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
            temp=Path(f.name);json.dump(data,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp:temp.unlink(missing_ok=True)

def valid_image(data):
    if not data or len(data)>MAX_IMAGE:raise ValueError('Use an image no larger than 10 MiB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as im:
                fmt=im.format
                if fmt not in ('JPEG','PNG') or getattr(im,'n_frames',1)!=1:raise ValueError('Only single-frame JPEG and PNG images are accepted.')
                im.verify()
            with Image.open(BytesIO(data)) as im:im.load()
    except Exception as exc:
        raise ValueError('Invalid, corrupted, unsupported or unsafe JPEG/PNG image.') from None
    return '.jpg' if fmt=='JPEG' else '.png'

def rows(doc):return doc if isinstance(doc,list) else doc['cases']
def frozen(doc):return not isinstance(doc,list) and doc.get('freeze_status')=='frozen'
def freeze_hash(doc):return sha(json.dumps({k:v for k,v in doc.items() if k!='frozen_manifest_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())

class DatasetStore:
    def __init__(self, root, datasets, lock):
        self.root=Path(root).resolve();self.datasets={k:Path(v) for k,v in datasets.items()};self.lock=lock
        self.lock_path=self.datasets[next(iter(self.datasets))].parent/'annotation-datasets'
    def path(self,key):
        if key not in self.datasets:raise ValueError('Unknown dataset.')
        return self.datasets[key]
    def load(self,key):return read(self.path(key))
    def editable(self,key,doc,revision):
        if key=='historical' or isinstance(doc,list):raise ValueError('Historical pilot is read-only.')
        if frozen(doc):raise ValueError('Dataset is frozen; edits and imports are rejected.')
        if self.load(key)[1]!=revision:raise ValueError('Dataset changed; reload before saving.')
    def image_path(self,value):
        if not isinstance(value,str) or Path(value).is_absolute():raise ValueError('Invalid relative image path.')
        p=(self.root/value).resolve()
        if not p.is_relative_to(self.root):raise ValueError('Image path escapes fixture root.')
        return p
    def inventory(self):
        result=[]
        for key,path in self.datasets.items():
            doc,_=read(path)
            for row in rows(doc):
                if row.get('image_path'):
                    p=self.image_path(row['image_path'])
                    if not p.is_file():raise ValueError('Registered image is missing: '+row['case_id'])
                    result.append((key,row,sha(p.read_bytes())))
        return result
    def validate(self,key):
        doc,_=self.load(key);rr=rows(doc)
        if isinstance(doc,list):
            return dict(total_cases=len(rr),images_present=sum(bool(r.get('image_path')) for r in rr),reviewed=sum(r.get('label_status') in ['reviewed','adjudicated'] for r in rr),benchmark_ready=0,errors=[],warnings=['Historical dataset is read-only; use its original validator for historical readiness.'],frozen=False)
        errors=[];warnings_out=[];ready=0;present=0;reviewed=0;all_hashes=[]
        try:inventory=self.inventory()
        except (ValueError,OSError) as exc:inventory=[];errors.append(str(exc))
        ids=[r.get('case_id') for r in rr]
        if len(ids)!=doc.get('target_image_count') or len(ids)!=len(set(ids)):errors.append('Case count or unique IDs invalid.')
        for r in rr:
            cid=r['case_id'];local=[]
            if r.get('image_path'):
                try:
                    data=self.image_path(r['image_path']).read_bytes();valid_image(data);present+=1;h=sha(data);all_hashes.append(h)
                    if h!=r.get('image_hash'):local.append('Image hash mismatch')
                    duplicates=[other['case_id'] for k,other,digest in inventory if digest==h and (k!=key or other['case_id']!=cid)]
                    if duplicates:local.append('Duplicate image with '+', '.join(duplicates))
                except (ValueError,OSError) as exc:local.append(str(exc))
            else:
                if r.get('image_hash'):local.append('Hash without image')
                warnings_out.append(cid+': image not imported')
            for otherkey,other,h in inventory:
                if otherkey==key:continue
                if any(r.get(f) and r.get(f)==other.get(f) for f in ['source_site_id','source_scene_id','site_scene_group']):local.append('Related site/scene crosses split: '+other['case_id']);break
                if r.get('original_image_id') and r.get('source_platform') and (r['original_image_id'],r['source_platform'])==(other.get('original_image_id'),other.get('source_platform')):local.append('Original source image reused across splits: '+other['case_id']);break
            if r.get('review_status') in ['reviewed','adjudicated']:
                reviewed+=1
                try:self.check_annotation(r)
                except ValueError as exc:local.append(str(exc))
            if r.get('site_identity_status')=='known' and not r.get('source_site_id'):local.append('Known site requires identifier')
            if r.get('scene_identity_status')=='known' and not r.get('source_scene_id'):local.append('Known scene requires identifier')
            eligibility=bool(r.get('image_path') and r.get('review_status') in ['reviewed','adjudicated'] and r.get('permission_verified') is True and r.get('license_or_provenance') and r.get('permission_evidence') and r.get('related_image_review_status')=='reviewed' and not local)
            if eligibility:ready+=1
            elif r.get('image_path'):
                blockers=[]
                if r.get('review_status') not in ['reviewed','adjudicated']:blockers.append('review_status must be reviewed/adjudicated')
                if local:blockers.append('resolve case validation errors')
                if r.get('permission_verified') is not True:blockers.append('permission_verified must be true')
                for field in ['license_or_provenance','permission_evidence']:
                    if not r.get(field):blockers.append(field+' is empty')
                if r.get('related_image_review_status')!='reviewed':blockers.append('related_image_review_status must be reviewed (current: '+str(r.get('related_image_review_status'))+')')
                purpose='development evaluation' if key=='development' else 'held-out evaluation/freeze'
                warnings_out.append(cid+': '+purpose+' blocked: '+'; '.join(blockers))
            if r.get('site_identity_status')=='unknown' and r.get('image_path'):warnings_out.append(cid+': site unknown; independence cannot be guaranteed')
            errors.extend(cid+': '+e for e in local)
        if frozen(doc) and doc.get('frozen_manifest_sha256')!=freeze_hash(doc):errors.append('Frozen manifest integrity mismatch.')
        return dict(total_cases=len(rr),images_present=present,missing_images=len(rr)-present,reviewed=reviewed,benchmark_ready=ready,duplicate_images=len(all_hashes)-len(set(all_hashes)),errors=errors,warnings=warnings_out,frozen=frozen(doc))
    def check_annotation(self,r):
        d=r.get('class_decisions')
        if not isinstance(d,dict) or set(d)!=set(HAZARDS) or any(v not in ['positive','negative','indeterminate'] for v in d.values()):raise ValueError('Explicit positive/negative/indeterminate decision required for all six classes.')
        if r.get('ground_truth_hazards')!=[h for h in HAZARDS if d[h]=='positive']:raise ValueError('Hazards must match positive class decisions.')
        if any(type(r.get(f)) is not bool for f in FLAGS[:-1]):raise ValueError('Explicit choices required for ambiguity and all three review concepts.')
        if 'indeterminate' in d.values() and (not r['ambiguous'] or not r['expected_uncertainty_review']):raise ValueError('Indeterminate classes require ambiguity and uncertainty review.')
        if any(not isinstance(r.get(f),str) or not r[f].strip() for f in ['reviewer','evidence_notes']):raise ValueError('Reviewer and evidence notes required.')
        if r.get('review_status')=='adjudicated' and not r.get('secondary_reviewer'):raise ValueError('Adjudicated status requires a secondary reviewer.')
    def mutate(self,key,revision,action):
        with self.lock(self.lock_path):
            doc,_=self.load(key);self.editable(key,doc,revision)
            action(doc)
            if self.load(key)[1]!=revision:raise ValueError('Manifest changed during edit.')
            atomic(self.path(key),doc)
        return self.validate(key)
    def save(self,key,cid,fields,revision):
        if not isinstance(fields,dict) or set(fields)-EDITABLE:raise ValueError('Unsupported/protected annotation fields.')
        def action(doc):
            r=next((r for r in rows(doc) if r['case_id']==cid),None)
            if r is None or not r.get('image_path'):raise ValueError('Import an image into this case first.')
            for k,v in fields.items():
                if k in TEXT and v is not None and not isinstance(v,str):raise ValueError('Text field must be text.')
                if k in FLAGS and v is not None and type(v) is not bool:raise ValueError('Invalid review flag.')
                if k in ENUMS and v not in ENUMS[k]:raise ValueError('Invalid status.')
                r[k]=v.strip() if isinstance(v,str) else v
            d=r.get('class_decisions')
            if not isinstance(d,dict) or set(d)!=set(HAZARDS) or any(v not in [None,'positive','negative','indeterminate'] for v in d.values()):raise ValueError('Invalid class decisions.')
            r['ground_truth_hazards']=[h for h in HAZARDS if d[h]=='positive'] if all(d.values()) else None
            if r.get('review_status') in ['reviewed','adjudicated']:self.check_annotation(r)
            for otherkey,other,digest in self.inventory():
                if otherkey == key:continue
                related = any(r.get(f) and r.get(f)==other.get(f) for f in ['source_site_id','source_scene_id','site_scene_group'])
                same_source = bool(r.get('source_platform') and r.get('original_image_id') and (r['source_platform'],r['original_image_id'])==(other.get('source_platform'),other.get('original_image_id')))
                if related or same_source:raise ValueError('Related site/scene or original image crosses split: '+other['case_id'])
        return self.mutate(key,revision,action)
    def upload(self,key,cid,encoded,revision):
        try:data=base64.b64decode(encoded,validate=True)
        except Exception:raise ValueError('Invalid image encoding.') from None
        ext=valid_image(data);digest=sha(data);created=[]
        def action(doc):
            duplicate=[r['case_id'] for k,r,h in self.inventory() if h==digest]
            if duplicate:raise ValueError('Duplicate image: '+', '.join(duplicate))
            r=next((r for r in rows(doc) if r['case_id']==cid),None)
            if r is None or r.get('image_path'):raise ValueError('Choose an empty case; existing images are never replaced.')
            directory=self.root/'fixtures/vision_v2'/('development' if key=='development' else 'heldout')
            directory=directory.resolve()
            if not directory.is_relative_to(self.root):raise ValueError('Invalid fixture folder.')
            directory.mkdir(parents=True,exist_ok=True);target=directory/(digest+ext)
            with target.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            created.append(target)
            r.update(image_path=target.relative_to(self.root).as_posix(),image_hash=digest,review_status='unreviewed')
        try:return self.mutate(key,revision,action)
        except Exception:
            # Only delete files created by this attempt, never any original image.
            for p in created:
                doc,_=self.load(key)
                if not any(r.get('image_hash')==digest for r in rows(doc)):p.unlink(missing_ok=True)
            raise
    def freeze(self,key,revision,acknowledged):
        if key!='heldout':raise ValueError('Only held-out datasets can be frozen.')
        if acknowledged is not True:raise ValueError('Confirm held-out access and grouping review before freezing.')
        def action(doc):
            result=self.validate(key)
            if result['errors'] or result['benchmark_ready']!=result['total_cases']:raise ValueError('All images, annotations, permissions and related-image reviews must pass before freezing.')
            doc.update(freeze_status='frozen',status='frozen',split_group_review_status='reviewed',frozen_at=datetime.now(timezone.utc).isoformat(),freeze_policy='SHA-256 of canonical UTF-8 JSON excluding frozen_manifest_sha256; no implicit unfreeze')
            doc['frozen_manifest_sha256']=freeze_hash(doc)
        return self.mutate(key,revision,action)
