"""Hand-reviewed views; no free text, identities, images, JSON payloads or configuration."""

VIEWS = {
    'safety_incidents': '''SELECT i.id, i.incident_code, i.project_id, p.name AS project_name,
        i.site_id, s.name AS site, ins.location_text AS location, h.hazard_type,
        i.risk_level, i.risk_score, i.status, i.created_at, i.closed_at,
        CASE WHEN i.status = 'CLOSED' AND i.closed_at >= i.created_at
          THEN (julianday(i.closed_at)-julianday(i.created_at))*24 END AS closure_hours,
        CASE WHEN a.total_actions = a.complete_actions AND a.last_completed >= a.first_created
          THEN (julianday(a.last_completed)-julianday(a.first_created))*24 END AS rectification_hours
        FROM incidents i JOIN projects p ON p.id=i.project_id JOIN sites s ON s.id=i.site_id
        JOIN inspections ins ON ins.id=i.inspection_id JOIN hazards h ON h.id=i.primary_hazard_id
        LEFT JOIN (SELECT incident_id, count(*) AS total_actions,
          sum(CASE WHEN status='COMPLETED' AND completed_at IS NOT NULL THEN 1 ELSE 0 END) AS complete_actions,
          min(created_at) AS first_created, max(completed_at) AS last_completed
          FROM corrective_actions GROUP BY incident_id) a ON a.incident_id=i.id''',
    'safety_hazards': '''SELECT h.id, ins.project_id, p.name AS project_name, ins.site_id, s.name AS site,
        ins.location_text AS location, h.hazard_type, h.risk_level, h.risk_score,
        ins.status AS inspection_status, h.created_at FROM hazards h
        JOIN inspections ins ON ins.id=h.inspection_id JOIN sites s ON s.id=ins.site_id
        JOIN projects p ON p.id=ins.project_id''',
}
COMMON = {'id','project_id','project_name','site_id','site','location','hazard_type','risk_level','risk_score','created_at'}
COLUMNS = {
    'safety_incidents': COMMON | {'incident_code','status','closed_at','closure_hours','rectification_hours'},
    'safety_hazards': COMMON | {'inspection_status'},
}
# SQLite authorizer permits only these base columns when accessed through our trusted views.
BASE_COLUMNS = {
    'incidents': {'id','incident_code','project_id','site_id','inspection_id','primary_hazard_id','risk_level','risk_score','status','created_at','closed_at'},
    'projects': {'id','name'}, 'sites': {'id','name'},
    'inspections': {'id','project_id','site_id','location_text','status'},
    'hazards': {'id','inspection_id','hazard_type','risk_level','risk_score','created_at'},
    'corrective_actions': {'incident_id','status','created_at','completed_at'},
}

def schema_context(view: str | None = None) -> dict:
    return {'views': {k: sorted(v) for k,v in COLUMNS.items() if view is None or k == view},
        'grain': {'safety_incidents':'One row per incident, joined to its primary hazard; action durations are pre-aggregated.',
                  'safety_hazards':'One row per observation, including unconfirmed and rejected inspections.'},
        'timestamps':'Stored UTC. Filter created_at using UTC start inclusive/end exclusive supplied by the application. Day grouping uses +8 hours.',
        'statuses':['OPEN','UNDER_REVIEW','RECTIFICATION','REINSPECTION','CLOSED','REJECTED'],
        'risk_levels':['LOW','MEDIUM','HIGH','CRITICAL'],
        'hazards':['missing_ppe','working_at_height','unprotected_edge','unsafe_scaffolding','electrical_hazard','housekeeping']}
