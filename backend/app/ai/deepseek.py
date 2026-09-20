"""DeepSeek Chat Completions JSON adapter; shared safety normalization stays in real.py."""
import json
from openai import OpenAI
from pydantic import ValidationError
from app.ai.real import RealMultimodalSafetyAIProvider
from app.ai.vision_contracts import VisualReinspectionOutput
from app.ai.prompts import REINSPECTION_PROMPT_VERSION
from app.ai.errors import AIProviderError
from app.ai.capabilities import validate
from app.ai.accounting import begin,capture,finish,normalize_error

class DeepSeekSafetyAIProvider(RealMultimodalSafetyAIProvider):
    model_provider='deepseek'
    def _create_client(self):
        validate('deepseek',self.model_name,'vision')
        key=self.config.deepseek_api_key
        if not key or not key.get_secret_value().strip():raise AIProviderError('missing_credentials','DEEPSEEK_API_KEY is required for the selected workload. No fallback was used.',503)
        return OpenAI(api_key=key.get_secret_value(),base_url='https://api.deepseek.com',timeout=self.config.ai_timeout_seconds,max_retries=0)

    def _request(self,prompt,content,schema):
        validate('deepseek',self.model_name,'vision')
        language=getattr(self,'output_language','en')
        prompt+=('\nPreferred output language: Simplified Chinese (zh-CN).' if language=='zh-CN' else '\nPreferred output language: English (en).')
        prompt+='\nUse the preferred language for titles, descriptions, evidence, recommendations and reasoning. Keep all enum values, codes, IDs, numeric fields and JSON keys unchanged. Keep regulation_queries in English for retrieval of the original indexed corpus. Never translate or invent official quotations.'
        user=[]
        for part in content:
            if part['type']=='input_text':user.append({'type':'text','text':part['text']})
            elif part['type']=='input_image':user.append({'type':'image_url','image_url':{'url':part['image_url'],'detail':part.get('detail','high')}})
            else:raise AIProviderError('invalid_provider_request','Unsupported DeepSeek input content part.',422)
        owned=self._injected_client is None
        client=self._injected_client or self._create_client()
        try:
            workflow='reinspection-analysis' if schema is VisualReinspectionOutput else 'inspection-analysis'
            version=REINSPECTION_PROMPT_VERSION if schema is VisualReinspectionOutput else self.prompt_version
            result=json_request(self,client,prompt,user,schema,workflow,version,self.config.ai_max_output_tokens,True,getattr(self,'validation_attempts',2))
            self.last_visual_output=result
            return result
        finally:
            if owned:client.close()

def json_request(owner,client,prompt,user,schema,workflow,version,max_tokens,has_images=False,attempts=1):
    # JSON mode guarantees JSON syntax, not schema adherence. Validate locally and reject extras.
    transport_prompt=prompt+'\nReturn only a JSON object matching this JSON schema:\n'+json.dumps(schema.model_json_schema())
    for attempt in range(attempts):
        record,started=begin(owner,workflow,version)
        try:
            response=client.chat.completions.create(model=owner.model_name,
                messages=[{'role':'system','content':transport_prompt+ ('\nThe prior response failed validation. Return a complete object matching the exact schema.' if attempt else '')},
                          {'role':'user','content':user}],response_format={'type':'json_object'},
                max_tokens=max_tokens,extra_body={'thinking':{'type':'disabled'}},stream=False)
            capture(record,response,has_images=has_images)
            if not response.choices or response.choices[0].finish_reason!='stop':raise ValueError('Incomplete output')
            result=schema.model_validate_json(response.choices[0].message.content or '')
            record['status']='SUCCEEDED'
            return result
        except (ValueError,ValidationError):
            record['error_message']='invalid_output'
            if attempt==attempts-1:raise AIProviderError('invalid_output','The selected provider returned invalid or incomplete JSON. No findings or answer were substituted.',502) from None
        except Exception as exc:
            error=normalize_error(exc);record['error_message']=error.code
            raise error from None
        finally:finish(record,started)
