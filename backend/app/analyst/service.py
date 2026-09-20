import json
import logging
import math
import re
import time
from app.core.config import settings
from app.analyst.localization import localize_answer, normalize_question
from app.db.session import utcnow
from app.analyst.contracts import AnalyticsAnswer, AnalyticsPlan, Chart, AnalystError
from app.analyst.interpreter import interpret, PERIODS
from app.analyst.metrics import METRICS, compile_query
from app.analyst.provider import propose, PROMPT_VERSION
from app.analyst.sql_safety import validate_sql, readonly_database, execute

logger=logging.getLogger(__name__)
NO_DATA='No matching safety records were found for this query and time period.'
UNSUPPORTED="This question cannot currently be answered from SafeSite's approved safety analytics data."

def display(value):
    return str(value).replace('_',' ').title()

def results_equal(first, second):
    if len(first)!=len(second): return False
    for a,b in zip(first,second):
        if set(a)!=set(b): return False
        for k in a:
            if isinstance(a[k],(int,float)) and isinstance(b[k],(int,float)):
                if not math.isclose(a[k],b[k],rel_tol=1e-8,abs_tol=1e-7): return False
            elif a[k]!=b[k]: return False
    return True

def present(answer, plan, rows, truncated):
    metric=METRICS[plan.metric]
    answer.rows=rows
    answer.rows_returned=len(rows)
    answer.truncated=truncated
    if not rows or (plan.metric!='incident_list' and
            all(r.get('sample_size',0)==0 or r.get('value') is None for r in rows)):
        answer.status='no_data'
        answer.answer=NO_DATA
        return
    answer.status='success'
    dims=list(plan.dimensions or metric.dimensions)
    answer.unit=metric.unit
    if plan.metric=='incident_list':
        answer.answer=f"Showing {len(rows)} matching incidents"+(' (limited to the newest 100).' if truncated else '.')
        answer.insight='Review the listed current statuses and initial risk scores before prioritizing follow-up.'
        kind='table'
    elif dims:
        first=rows[0]
        answer.key_metric=round(first['value'],2)
        # IDs keep same-named sites distinct in both summaries and charts.
        label=' / '.join(display(first.get(d,'')) for d in dims)
        if 'site_id' in first: label+=f" (site #{first['site_id']})"
        if 'day' in dims:
            answer.key_metric=None
            answer.answer=f"{display(plan.metric)} is shown for {len(rows)} returned time groups."
            answer.insight='Rows are grouped by recorded creation day. Missing dates are not interpolated and no forecast is inferred.'
        else:
            ties=sum(math.isclose(r['value'],first['value']) for r in rows)
            answer.answer=f"{label}: {first['value']:,.2f} {metric.unit}, "+('joint highest in the returned groups.' if ties>1 else 'highest in the returned groups.')
            answer.insight=f"This group has {first['sample_size']} matching records supporting the metric."
            if plan.metric=='recurring_hazard_count':
                answer.insight=f"The leading group has {first['sample_size']} occurrences; {int(first['value'])} are beyond its first occurrence."
        kind='line' if dims==['day'] else ('bar' if len(dims)==1 and len(rows)<=20 else 'table')
    else:
        value=rows[0]['value']
        answer.key_metric=round(value,2)
        answer.answer=f"{display(plan.metric)}: {value:,.2f} {metric.unit}."
        answer.insight=f"Calculated from {rows[0]['sample_size']} qualifying records in the selected creation cohort."
        kind='metric'
    if truncated:
        answer.assumptions.append('Output is limited to 100 rows/groups. Comparisons describe returned data only; narrow the period or filters for complete results.')
    chart_rows=[dict(r) for r in rows]
    if kind=='bar':
        for row in chart_rows:
            row['label']=' / '.join(display(row.get(d,'')) for d in dims)
            if 'site_id' in row: row['label']+=f" (#{row['site_id']})"
    answer.chart=Chart(type=kind,xKey='day' if kind=='line' else 'label' if kind=='bar' else None,
        yKey='value' if kind in ('bar','line') else None,data=chart_rows)

class SafetyAnalystService:
    def __init__(self,engine,*,planner=None,now=None):
        self.engine=engine
        self.planner=planner
        self.now=now or utcnow()

    def ask(self,question,language='en'):
        start=time.perf_counter()
        answer=AnalyticsAnswer(status='unsupported',question=question,answer=UNSUPPORTED)
        plan=None
        calls=[]
        event={'question':question,'policy':'safety-metrics-v1','prompt_version':PROMPT_VERSION}
        try:
            plan=interpret(question)
            if plan is None:
                if not re.search(r'\b(incidents?|hazards?|safety|rectification|risk|sites?|closure)\b|\u9690\u60a3|\u4e8b\u4ef6|\u5b89\u5168|\u6574\u6539|\u5de5\u5730|\u98ce\u9669|\u5173\u95ed',question,re.I):
                    return answer
                if self.planner:
                    answer.provider='test'
                    answer.model='injected-test-planner'
                    plan=self.planner(question,self.now)
                elif settings.analyst_provider in ('openai','deepseek'):
                    answer.provider=settings.analyst_provider
                    answer.model=settings.analyst_model
                    plan=propose(question,self.now,language=language,call_records=calls)
                else:
                    return answer
                plan=AnalyticsPlan.model_validate(plan.model_dump())
                if not plan.supported: return answer
                mentioned=[p for p in PERIODS if p in normalize_question(question).lower()]
                if mentioned and plan.time_range!=mentioned[0]:
                    raise AnalystError('rejected','The generated plan did not preserve the requested time period.')
            if not plan.supported: return answer
            canonical,period,assumptions=compile_query(plan,self.now)
            answer.metric=plan.metric
            answer.metric_definition=METRICS[plan.metric].definition
            answer.time_range=period
            answer.assumptions=assumptions
            dimensions=plan.dimensions or list(METRICS[plan.metric].dimensions)
            answer.interpretation=display(plan.metric)+(' by '+', '.join(dimensions) if dimensions else '')+'. Filters: '+(
                ', '.join(f'{k}={v}' for k,v in plan.filters.model_dump().items() if v not in (None,False)) or 'none')+'.'
            generated=answer.provider!='deterministic'
            if generated and not plan.sql.strip():
                raise AnalystError('rejected','The model did not propose SQL for its plan.')
            candidate=plan.sql if generated else canonical
            event.update(metric=plan.metric,path=answer.provider,proposed_sql=candidate)
            safe=validate_sql(candidate)
            answer.validation='sql_passed'
            with readonly_database(self.engine) as connection:
                rows,truncated=execute(connection,safe)
                if generated:
                    reference,reference_truncated=execute(connection,canonical)
                    if truncated!=reference_truncated or not results_equal(rows,reference):
                        raise AnalystError('rejected','Generated SQL results did not match the registered metric and filters. No answer was returned.')
            answer.sql=safe
            answer.validation='passed; metric results verified'
            present(answer,plan,rows,truncated)
            return answer
        except AnalystError as exc:
            answer.status=exc.status
            answer.answer=str(exc)
            answer.validation='rejected' if exc.status=='rejected' else answer.validation
            return answer
        except Exception:
            answer.status='error'
            answer.answer='Safety analytics could not complete. No operational records were changed and no answer was fabricated.'
            return answer
        finally:
            answer.latency_ms=round((time.perf_counter()-start)*1000)
            event.update(status=answer.status,provider=answer.provider,model=answer.model,
                validation=answer.validation,latency_ms=answer.latency_ms,rows_returned=answer.rows_returned)
            # JSON escapes control characters. Never record SDK errors, credentials or internal prompts.
            payload=json.dumps(event,ensure_ascii=True)
            for key in (settings.openai_api_key,settings.deepseek_api_key):
                if key and key.get_secret_value():payload=payload.replace(key.get_secret_value(),'[redacted]')
            payload=re.sub(r'sk-[A-Za-z0-9_-]+','[redacted]',payload)
            logger.info('safety_analytics %s',payload)
            if calls:
                from sqlalchemy.orm import Session
                from types import SimpleNamespace
                from app.models.entities import AIExecution
                from app.ai.accounting import attach
                execution=AIExecution(workflow_name='safety-analyst',model_provider=answer.provider,model_name=answer.model,
                    prompt_version=PROMPT_VERSION,policy_version='safety-metrics-v1',latency_ms=answer.latency_ms,
                    status=answer.status.upper(),error_message=None if answer.status in ('success','no_data') else 'planning_or_validation_'+answer.status,
                    entity_type='analytics',entity_id=0)
                attach(execution,SimpleNamespace(call_records=calls))
                with Session(self.engine) as log_db:
                    log_db.add(execution);log_db.commit()
            localize_answer(answer,language,plan)
