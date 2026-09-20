"""Prepare one clearly labeled offline uncertainty fixture in the isolated Day 1 DB."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT/'backend');sys.path.insert(0,str(ROOT/'backend'))
os.environ.update(DATABASE_URL='sqlite:///./data/day1-demo.db',UPLOAD_DIR='./data/day1-uploads',SAFESITE_AI_PROVIDER='mock',SAFESITE_VISION_PROVIDER='mock',SAFESITE_REINSPECTION_PROVIDER='mock')
import httpx
from app.ai.mock import MockSafetyAIProvider
from app.db.session import SessionLocal
from app.models.entities import Inspection
from app.services import workflow

class UncertainFixture(MockSafetyAIProvider):
    model_name='offline-uncertainty-fixture'
    def analyze_inspection(self,**kw):
        result=super().analyze_inspection(**kw)
        result.hazards=result.hazards[:1]
        h=result.hazards[0];h.confidence=.55
        h.title='Possible elevated activity ? OFFLINE FIXTURE'
        h.description='Synthetic uncertainty response for a human review demonstration; not image inference.'
        h.visual_evidence=['MOCK fixture: visibility does not establish the work position or protection requirement.']
        result.overall_confidence=.55;result.requires_human_review=True
        result.summary='OFFLINE MOCK: ambiguous observation; do not infer site safety.'
        result.reasoning_notes=['MOCK: prepared uncertainty scenario, no model call or image understanding.','Insufficient evidence; a qualified person must review before any incident decision.']
        return result

def main():
    image=ROOT/'evaluation/fixtures/live_smoke/03_ambiguous.jpg'
    with httpx.Client(base_url='http://127.0.0.1:8002/api/v1',timeout=30) as client:
        health=client.get('/health');health.raise_for_status()
        if health.json()['ai_mode']!='mock':raise RuntimeError('Mock Day 1 backend required')
        with image.open('rb') as f:
            upload=client.post('/uploads',files={'file':(image.name,f,'image/jpeg')});upload.raise_for_status()
        projects=client.get('/projects').json();project=projects[0];site=project['sites'][0]
        response=client.post('/inspections',json=dict(project_id=project['id'],site_id=site['id'],location_text='DAY1 B ? OFFLINE uncertainty fixture',source_type='IMAGE',image_path=upload.json()['image_path']))
        response.raise_for_status();ident=response.json()['id']
    with SessionLocal() as db:
        item=db.get(Inspection,ident)
        if item is None:raise RuntimeError('Day 1 backend must use day1-demo.db')
        workflow.analyze(db,item,UncertainFixture());db.commit()
    print('Prepared DEMO_AI uncertainty inspection',ident,'in isolated day1-demo.db; zero model calls.')
if __name__=='__main__':main()
