"""Explicitly authorized single-image connectivity verification; never a benchmark."""
import base64,hashlib,json,logging,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'));os.chdir(ROOT/'backend')
logging.disable(logging.CRITICAL)

def main():
 if sys.argv[1:]!=['--execute']:raise ValueError('Explicit --execute required')
 from app.core.config import settings
 from app.ai.real import RealMultimodalSafetyAIProvider
 from app.ai.images import image_data_url
 assert settings.vision_provider=='openai' and settings.vision_model=='gpt-5.6-sol'
 assert settings.openai_api_key and settings.openai_api_key.get_secret_value().strip()
 settings.upload_dir=ROOT/'evaluation/fixtures/live_smoke'
 path=settings.upload_dir/'01_safe.jpg'; original=hashlib.sha256(path.read_bytes()).hexdigest()
 data=image_data_url('/uploads/01_safe.jpg')
 out=ROOT/'evaluation/reports/openai_connectivity_check';out.mkdir(exist_ok=True)
 with (out/'execution.lock').open('x') as f:f.write('One attempt authorized; never automatically rerun.')
 result=dict(attempts=0,success=False,requested_model='gpt-5.6-sol',prompt_version='vision-v1')
 def save():(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 p=RealMultimodalSafetyAIProvider();p.validation_attempts=1;c=p._create_client();assert c.max_retries==0
 def before(request):
  assert result['attempts']==0 and str(request.url)=='https://api.openai.com/v1/responses'
  body=json.loads(request.content)
  images=[i for m in body['input'] if isinstance(m.get('content'),list) for i in m['content'] if i.get('type')=='input_image']
  assert len(images)==1 and images[0]['image_url']==data
  result['image_bytes_verified']=True;result['attempts']=1;save()
 c._client.event_hooks['request']=[before];p._injected_client=c
 try:
  answer=p.analyze_inspection(location='',description=None,image_path='/uploads/01_safe.jpg')
  result.update(success=True,analysis=answer.model_dump(mode='json'),raw_visual_output=p.last_visual_output.model_dump(mode='json'))
 except Exception as e:result['error']=getattr(e,'code',type(e).__name__)
 finally:
  c.close();result['call_records']=p.call_records;result['original_unchanged']=hashlib.sha256(path.read_bytes()).hexdigest()==original;save()
 print(json.dumps({k:v for k,v in result.items() if k not in ['analysis','raw_visual_output']},indent=2))
if __name__=='__main__':main()
