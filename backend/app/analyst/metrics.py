from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from app.analyst.contracts import AnalyticsPlan, AnalystError

LOCAL = timezone(timedelta(hours=8), name='Asia/Hong_Kong')
ACTIVE = "status NOT IN ('CLOSED', 'REJECTED')"

@dataclass(frozen=True)
class Metric:
    definition: str
    expression: str = 'COUNT(*)'
    predicate: str = "status != 'REJECTED'"
    view: str = 'safety_incidents'
    unit: str = 'incidents'
    dimensions: tuple = ()

METRICS = {
    'total_incidents': Metric('Count all incidents, including rejected records.', predicate='1 = 1'),
    'open_incidents': Metric('Count currently unresolved incidents: OPEN, UNDER_REVIEW, RECTIFICATION or REINSPECTION.', predicate=ACTIVE),
    'critical_incidents': Metric('Count currently unresolved incidents with initial CRITICAL risk.', predicate=ACTIVE+" AND risk_level = 'CRITICAL'"),
    'closed_incidents': Metric('Count incidents currently CLOSED.', predicate="status = 'CLOSED'"),
    'closure_rate': Metric('Currently CLOSED / all non-REJECTED incidents in the creation cohort, multiplied by 100.', "100.0 * SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)", unit='%'),
    'average_rectification_time': Metric('Mean elapsed hours from earliest corrective-action creation to latest completion, only where every action has a completed timestamp. Excludes rejected incidents. This is an action-resolution duration proxy, not measured time actively working.', 'AVG(rectification_hours)', "status != 'REJECTED' AND rectification_hours IS NOT NULL", unit='hours'),
    'hazard_count': Metric('Count all recorded hazard observations, including unconfirmed or rejected inspections; not a count of confirmed incidents.', predicate='1 = 1',view='safety_hazards',unit='observations'),
    'hazard_distribution': Metric('Count recorded hazard observations by hazard type, including unconfirmed/rejected inspections.',predicate='1 = 1',view='safety_hazards',unit='observations',dimensions=('hazard_type',)),
    'incident_count_by_site': Metric('Count non-rejected incidents by site, using current status and initial risk.',dimensions=('site',)),
    'incident_count_by_risk_level': Metric('Count non-rejected incidents by initial risk level.',dimensions=('risk_level',)),
    'recurring_hazard_count': Metric('Extra incidents beyond the first occurrence of the same primary hazard type at the same site within the creation cohort. Excludes rejected incidents; a repeated observation is not proof of a recurring physical defect.', 'COUNT(*) - 1',dimensions=('site','hazard_type'),unit='repeat incidents'),
    'critical_incident_rate': Metric('Initial CRITICAL incidents / all non-rejected incidents in the creation cohort, multiplied by 100.', "100.0 * SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)",unit='%'),
    'average_risk_score': Metric('Mean initial risk score of currently unresolved incidents; matches the dashboard population before rounding.', 'AVG(risk_score)',ACTIVE,unit='risk points'),
    'unresolved_incident_count': Metric('Count OPEN, UNDER_REVIEW, RECTIFICATION and REINSPECTION incidents; excludes CLOSED and REJECTED.',predicate=ACTIVE),
    'unresolved_incident_rate': Metric('Currently unresolved / all non-rejected incidents in the creation cohort, multiplied by 100.', "100.0 * SUM(CASE WHEN status != 'CLOSED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)",unit='%'),
    'average_closure_time': Metric('Mean hours from incident creation to human closure, only CLOSED incidents with valid timestamps.', 'AVG(closure_hours)', "status = 'CLOSED' AND closure_hours IS NOT NULL",unit='hours'),
    'incident_volume': Metric('Count non-rejected incidents by Hong Kong creation day; absent days have no recorded incidents.',dimensions=('day',)),
    'incident_list': Metric('List non-rejected incidents with current status and initial risk; newest first.'),
}

def time_bounds(period: str, now: datetime):
    now = now.astimezone(LOCAL)
    day = now.replace(hour=0,minute=0,second=0,microsecond=0)
    start = None
    end = now
    if period == 'today': start = day
    elif period == 'this week': start = day-timedelta(days=day.weekday())
    elif period == 'this month': start = day.replace(day=1)
    elif period == 'last 7 days': start = now-timedelta(days=7)
    elif period == 'last 30 days': start = now-timedelta(days=30)
    elif period == 'previous month':
        end = day.replace(day=1)
        start = (end-timedelta(days=1)).replace(day=1)
    return (start.astimezone(timezone.utc) if start else None, end.astimezone(timezone.utc))

def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

def compile_query(plan: AnalyticsPlan, now: datetime) -> tuple[str, str, list[str]]:
    metric = METRICS[plan.metric]
    dims = list(plan.dimensions or metric.dimensions)
    if len(set(dims)) != len(dims):
        raise AnalystError('unsupported','Duplicate dimensions are unsupported.')
    if plan.metric == 'recurring_hazard_count' and dims != ['site','hazard_type']:
        raise AnalystError('unsupported','Recurring hazards require both site and hazard type.')
    if plan.metric == 'incident_list' and dims:
        raise AnalystError('unsupported','Incident lists cannot be grouped.')
    predicates = [metric.predicate]
    start,end = time_bounds(plan.time_range,now)
    # datetime adapter format matches UTCDateTime storage (naive UTC, fixed microseconds).
    stamp = lambda d: literal(d.replace(tzinfo=None).isoformat(' ',timespec='microseconds'))
    if start: predicates.append('created_at >= '+stamp(start))
    predicates.append('created_at < '+stamp(end))
    for name,value in plan.filters.model_dump().items():
        if name == 'unresolved_only':
            if value:
                if metric.view != 'safety_incidents':
                    raise AnalystError('unsupported','Unresolved status requires an incident metric.')
                predicates.append(ACTIVE)
            continue
        if value is not None:
            column = 'site' if name == 'site_name' else name
            if column == 'status' and metric.view == 'safety_hazards':
                raise AnalystError('unsupported','Incident status cannot filter observation metrics. Ask about incidents instead.')
            predicates.append(column+' = '+literal(value))
    groups = []
    for dim in dims:
        if dim == 'site': groups += ['site_id','site']
        elif dim == 'location': groups += ['site_id','site','location']
        elif dim == 'day': groups += ["DATE(created_at, '+8 hours')"]
        else: groups.append(dim)
    groups = list(dict.fromkeys(groups))
    labels = [g+' AS day' if g.startswith('DATE') else g for g in groups]
    if plan.metric == 'incident_list':
        fields = 'id, incident_code, site, location, hazard_type, risk_level, risk_score, status, created_at'
    else:
        fields = ', '.join(labels+[metric.expression+' AS value','COUNT(*) AS sample_size'])
    sql = f"SELECT {fields} FROM {metric.view} WHERE " + ' AND '.join('('+p+')' for p in predicates)
    if groups: sql += ' GROUP BY '+', '.join(groups)
    if plan.metric == 'recurring_hazard_count': sql += ' HAVING COUNT(*) > 1'
    if plan.metric == 'incident_list': sql += ' ORDER BY created_at DESC, id DESC'
    elif groups: sql += ' ORDER BY '+('day ASC' if 'day' in dims else 'value DESC, '+', '.join(groups))
    sql += ' LIMIT 100'
    range_label = f"{plan.time_range}: {start.astimezone(LOCAL).isoformat() if start else 'available history'} to {end.astimezone(LOCAL).isoformat()} (end exclusive)"
    assumptions = ['Dates use Hong Kong time (UTC+08:00); weeks start Monday. Last N days are rolling N x 24 hours.',
        'Time filters select record creation cohorts. Status is current and risk is the initial recorded score.',
        'Results include demo and user-created records in this database. No claim is made that seeded records are real field observations.']
    return sql,range_label,assumptions
