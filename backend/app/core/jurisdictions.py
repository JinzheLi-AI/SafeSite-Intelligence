from sqlalchemy import inspect, text, select
from app.models.entities import Project

# Storage labels of reviewed corpora are preserved; project context uses canonical codes.
SOURCE_JURISDICTIONS={'HK-SAR':'Hong Kong'}
JURISDICTIONS=[
    {'code':'HK-SAR','name':'Hong Kong SAR','supported':True,'authority':'Hong Kong Labour Department'},
    {'code':'CN','name':'Mainland China','supported':False,'authority':None},
    {'code':'SG','name':'Singapore','supported':False,'authority':None},
    {'code':'MY','name':'Malaysia','supported':False,'authority':None},
]

def ensure_project_jurisdiction(engine):
    """One additive, idempotent upgrade for existing SQLite pilot databases; no row reset."""
    if engine.dialect.name=='sqlite' and 'projects' in inspect(engine).get_table_names():
        with engine.begin() as connection:
            columns={c['name'] for c in inspect(connection).get_columns('projects')}
            if 'regulatory_jurisdiction' not in columns:
                connection.execute(text("ALTER TABLE projects ADD COLUMN regulatory_jurisdiction VARCHAR(20) NOT NULL DEFAULT 'HK-SAR'"))

def project_context(db,project_id=None):
    project=db.get(Project,project_id) if project_id is not None else db.scalar(select(Project).order_by(Project.id))
    code=project.regulatory_jurisdiction if project else None
    definition=next((j for j in JURISDICTIONS if j['code']==code),None)
    return {'project_id':project.id if project else None,'project_name':project.name if project else None,
        'regulatory_jurisdiction':code,'name':definition['name'] if definition else code or 'No active project',
        'supported':bool(definition and definition['supported']),
        'authority':definition['authority'] if definition else None,'options':JURISDICTIONS}
