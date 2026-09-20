"""Workload-local planning transport; SQL execution never occurs here."""
from openai import OpenAI
from app.ai.capabilities import validate,key_for
from app.ai.accounting import begin,capture,finish,normalize_error
from app.ai.errors import AIProviderError
from app.ai.deepseek import json_request
from app.analyst.contracts import AnalyticsPlan

class AnalystProvider:
    def __init__(self,config,client=None):
        self.config=config;self.client=client;self.model_provider=config.analyst_provider if config.analyst_provider!='deterministic' else 'openai'
        self.model_name=config.analyst_model;self.call_records=[]
    def request(self,prompt,question,version):
        owned=self.client is None
        if owned:
            validate(self.model_provider,self.model_name,'analyst')
            key=key_for(self.config,self.model_provider)
            if not key or not key.get_secret_value().strip():raise AIProviderError('missing_credentials',('DEEPSEEK_API_KEY' if self.model_provider=='deepseek' else 'OPENAI_API_KEY')+' is required for flexible planning. Common semantic questions remain available.',503)
            client=OpenAI(api_key=key.get_secret_value(),base_url={'openai':'https://api.openai.com/v1','deepseek':'https://api.deepseek.com'}[self.model_provider],
                          timeout=self.config.analyst_timeout_seconds,max_retries=0)
        else:client=self.client
        try:
            if self.model_provider=='deepseek':return json_request(self,client,prompt,question,AnalyticsPlan,'safety-analyst',version,5000)
            row,started=begin(self,'safety-analyst',version)
            try:
                result=client.responses.parse(model=self.model_name,store=False,max_output_tokens=5000,
                    input=[{'role':'system','content':prompt},{'role':'user','content':question}],text_format=AnalyticsPlan)
                capture(row,result)
                if result.status!='completed' or result.output_parsed is None:raise AIProviderError('invalid_output','The analyst model returned no complete structured plan. No answer was fabricated.',502)
                plan=AnalyticsPlan.model_validate(result.output_parsed.model_dump());row['status']='SUCCEEDED';return plan
            except Exception as exc:
                error=normalize_error(exc);row['error_message']=error.code;raise error from None
            finally:finish(row,started)
        finally:
            if owned:client.close()

def get_analyst_provider(config,client=None):return AnalystProvider(config,client)
