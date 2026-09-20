"""Non-inference connectivity check; no credentials sent, no response bodies logged."""
import json,os,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'));os.chdir(ROOT/'backend')
from app.ai.real import RealMultimodalSafetyAIProvider
print('dns_resolved',bool(socket.getaddrinfo('api.openai.com',443)))
c=RealMultimodalSafetyAIProvider()._create_client()
try:
 r=c._client.get('https://api.openai.com/v1/models',timeout=15)
 print('unauthenticated_https_status',r.status_code)
 print('tls_verified',True)
except Exception as e:
 seen=set()
 while e and id(e) not in seen:
  seen.add(id(e));print(json.dumps(dict(type=type(e).__name__,errno=getattr(e,'errno',None),winerror=getattr(e,'winerror',None))));e=e.__cause__ or e.__context__
 sys.exit(1)
finally:c.close()
