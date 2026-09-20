"""Deliberately narrow English routing. Unrecognized qualifiers never silently disappear."""
import re
from app.analyst.localization import normalize_question
from app.analyst.contracts import AnalyticsPlan, Filters, AnalystError

BLOCKED = re.compile(r"\b(delete|drop|update|insert|alter|create\s+table|replace|vacuum|attach|detach|pragma|sqlite_master|sqlite_schema|writable_schema|load_extension|readfile|writefile|password|secret|api.?keys?)\b|--|/\*|;|ignore\s+(all\s+)?previous",re.I)
PERIODS = ['previous month','last 30 days','last 7 days','this month','this week','today']
HAZARDS = {'working at height':'working_at_height','work at height':'working_at_height','missing ppe':'missing_ppe',
    'unprotected edge':'unprotected_edge','unsafe scaffolding':'unsafe_scaffolding','electrical hazard':'electrical_hazard',
    'housekeeping':'housekeeping'}

def interpret(question: str) -> AnalyticsPlan | None:
    if BLOCKED.search(question) or re.search(r'\u5220\u9664|\u6e05\u7a7a|\u66f4\u65b0|\u5199\u5165|\u9644\u52a0\u6570\u636e\u5e93|\u5ffd\u7565.*\u89c4\u5219|\u4fee\u6539.*\u72b6\u6001',question):
        raise AnalystError('rejected','Only read-only safety analytics questions are allowed. No operational records were changed.')
    question=normalize_question(question)
    q=re.sub(r'\s+',' ',question.lower().replace('-',' ').replace('_',' ')).strip(' ?.!')
    periods=[p for p in PERIODS if p in q]
    if len(periods)>1:
        raise AnalystError('unsupported','Please ask about one supported time period at a time.')
    period=periods[0] if periods else 'all'
    if periods: q=q.replace('the '+periods[0],'').replace(periods[0],'').strip()
    # A precise site/project filter can be supplied using quotes, including unknown names (no-data).
    filters=Filters()
    for kind,field in [('site','site_name'),('project','project_name')]:
        match=re.search(r'\b(?:at|for|in) '+kind+r' "([^"]+)"',q)
        if match:
            # Preserve spelling from original input.
            original=re.search(r'\b(?:at|for|in) '+kind+r' "([^"]+)"',question,re.I)
            setattr(filters,field,original.group(1))
            q=q.replace(match.group(0),'')
    question=normalize_question(question)
    q=re.sub(r'\s+',' ',q).strip()
    # Avoid dropping an unsupported date, location, negation, or other trailing qualifier.
    patterns=[
        (r'(what is (our |the )?)?most common hazard( (type|category))?', 'hazard_distribution', []),
        (r'which (site|location) has the (most critical incidents|highest critical risk count)', 'critical_incidents', ['site']),
        (r'(what is (our |the )?)?(incident )?closure rate', 'closure_rate', []),
        (r'(what is (the |our )?)?average rectification time', 'average_rectification_time', []),
        (r'which hazards are recurring', 'recurring_hazard_count', []),
        (r'(compare|show) hazard counts across sites', 'hazard_count', ['site']),
        (r'which location has the highest average risk score', 'average_risk_score', ['location']),
        (r'how has incident volume changed over time', 'incident_volume', []),
        (r'which hazards take longest to close', 'average_closure_time', ['hazard_type']),
        (r'what percentage of incidents are currently unresolved', 'unresolved_incident_rate', []),
        (r'which risk category is most common', 'incident_count_by_risk_level', []),
        (r'(show|list) (open )?critical incidents( (created( in| from)?|from|in|over))?', 'incident_list', []),
        (r'(how many|count|show) (total |open |closed |critical |unresolved )?incidents( (occurred|created|from|in|over))?', 'total_incidents', []),
        (r'(what is (our |the )?)?critical incident rate', 'critical_incident_rate', []),
        (r'(what is (our |the )?)?average risk score', 'average_risk_score', []),
        (r'(how many|count) hazards( (occurred|recorded|from|in|over))?', 'hazard_count', []),
    ]
    # Optional hazard subtype on count/list questions.
    for words,kind in HAZARDS.items():
        if words in q and re.match(r'(how many|count|show|list)\b',q):
            filters.hazard_type=kind
            q=q.replace(words+' ','')
            break
    for pattern,metric,dimensions in patterns:
        if re.fullmatch(pattern,q):
            if metric=='total_incidents':
                for token,name in [('open','open_incidents'),('closed','closed_incidents'),('critical','critical_incidents'),('unresolved','unresolved_incident_count')]:
                    if re.search(r'\b'+token+r'\b',q): metric=name
            if metric=='incident_list':
                filters.risk_level='CRITICAL'
                # Open here means all four unresolved states, handled by service compilation.
                if 'open ' in q: filters.unresolved_only=True
            return AnalyticsPlan(metric=metric,dimensions=dimensions,filters=filters,time_range=period,
                interpreted_question=question,explanation='Matched a reviewed semantic question.')
    return None
