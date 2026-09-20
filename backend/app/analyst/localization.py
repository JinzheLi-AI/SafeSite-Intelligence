"""Bilingual presentation of the same verified metric result; SQL and rows stay unchanged."""
import re
from app.core.localization import dictionary, tr

def normalize_question(question):
    normalized=question.strip().rstrip('？?。.!')
    for english,chinese in dictionary('zh-CN').items():
        if english.startswith(('What ','Which ','Show ','Compare ','How ')) and normalized==chinese.rstrip('？?。.!'):
            return english
    return question

def localize_answer(answer,language,plan=None):
    fields=['answer','insight','metric_definition','unit','assumptions']
    english={name:getattr(answer,name) for name in fields}
    chinese={name:([tr(x,'zh-CN') for x in value] if isinstance(value,list) else tr(value,'zh-CN')) for name,value in english.items()}
    # The interpretation uses canonical codes in technical details, with translated labels around them.
    from app.analyst.metrics import METRICS
    if plan and answer.metric:
        dimensions=plan.dimensions or list(METRICS[plan.metric].dimensions)
        filters=', '.join(tr(k,'zh-CN')+'='+tr(str(v),'zh-CN') for k,v in plan.filters.model_dump().items() if v not in (None,False)) or tr('none','zh-CN')
        chinese['interpretation']=tr(answer.metric,'zh-CN')+(' / '+', '.join(tr(d,'zh-CN') for d in dimensions) if dimensions else '')+'; '+tr('Filters','zh-CN')+': '+filters
    else:
        chinese['interpretation']=''
    for key in ['answer','insight']:
        for term in ['Working At Height','Unprotected Edge','Missing Ppe','Unsafe Scaffolding','Electrical Hazard','Housekeeping']:
            chinese[key]=chinese[key].replace(term,tr(term,'zh-CN'))
        chinese[key]=chinese[key].replace('site #',tr('site','zh-CN')+' #')
    # Preserve exact ISO bounds; translate only the period and explanation labels.
    period=answer.time_range
    for source in ['previous month','last 30 days','last 7 days','this month','this week','today','all','available history','to','end exclusive']:
        period=re.sub(r'\b'+re.escape(source)+r'\b',lambda m:tr(source,'zh-CN'),period)
    chinese['time_range']=period
    english.update(interpretation=answer.interpretation,time_range=answer.time_range)
    answer.localized={'en':english,'zh-CN':chinese}
    if language=='zh-CN':
        for key,value in chinese.items(): setattr(answer,key,value)
