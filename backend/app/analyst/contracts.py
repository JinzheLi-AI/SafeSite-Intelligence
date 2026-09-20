from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

MetricName = Literal['total_incidents', 'open_incidents', 'critical_incidents', 'closed_incidents',
    'closure_rate', 'average_rectification_time', 'hazard_count', 'hazard_distribution',
    'incident_count_by_site', 'incident_count_by_risk_level', 'recurring_hazard_count',
    'critical_incident_rate', 'average_risk_score', 'unresolved_incident_count',
    'unresolved_incident_rate', 'average_closure_time', 'incident_volume', 'incident_list']
Dimension = Literal['site', 'hazard_type', 'risk_level', 'day', 'location']
Period = Literal['all', 'today', 'this week', 'this month', 'last 7 days', 'last 30 days', 'previous month']
HazardType = Literal['missing_ppe','working_at_height','unprotected_edge','unsafe_scaffolding','electrical_hazard','housekeeping']
Risk = Literal['LOW','MEDIUM','HIGH','CRITICAL']
Status = Literal['OPEN','UNDER_REVIEW','RECTIFICATION','REINSPECTION','CLOSED','REJECTED']

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Filters(StrictModel):
    unresolved_only: bool = False
    site_name: str | None = Field(default=None, max_length=200)
    project_name: str | None = Field(default=None, max_length=200)
    hazard_type: HazardType | None = None
    risk_level: Risk | None = None
    status: Status | None = None

class AnalyticsPlan(StrictModel):
    supported: bool = True
    interpreted_question: str = Field(default='', max_length=1000)
    metric: MetricName = 'total_incidents'
    dimensions: list[Dimension] = Field(default_factory=list, max_length=2)
    filters: Filters = Field(default_factory=Filters)
    time_range: Period = 'all'
    sql: str = Field(default='', max_length=12000)
    visualization_type: Literal['metric','bar','line','table'] = 'metric'
    explanation: str = Field(default='', max_length=1000)

class AskRequest(StrictModel):
    language: Literal['en','zh-CN'] | None = None
    question: str = Field(min_length=3, max_length=1000)

Scalar = str | int | float | None

class Chart(StrictModel):
    type: Literal['metric','bar','line','table']
    xKey: str | None = None
    yKey: str | None = None
    data: list[dict[str, Scalar]] = Field(max_length=100)

    @model_validator(mode='after')
    def verify_axes(self):
        if self.type in ('bar','line'):
            if not self.xKey or not self.yKey or any(self.xKey not in r or
                not isinstance(r.get(self.yKey),(int,float)) for r in self.data):
                raise ValueError('Chart axes must reference actual numeric query results.')
        return self

class AnalyticsAnswer(StrictModel):
    localized: dict[str, dict[str, Any]] = Field(default_factory=dict)
    status: Literal['success','no_data','unsupported','rejected','unavailable','error']
    question: str
    answer: str
    insight: str = ''
    interpretation: str = ''
    metric: str | None = None
    metric_definition: str = ''
    time_range: str = ''
    timezone: str = 'Asia/Hong_Kong (UTC+08:00)'
    assumptions: list[str] = Field(default_factory=list)
    key_metric: Scalar = None
    unit: str = ''
    chart: Chart | None = None
    rows: list[dict[str, Scalar]] = Field(default_factory=list, max_length=100)
    sql: str | None = None
    rows_returned: int = 0
    truncated: bool = False
    provider: str = 'deterministic'
    model: str | None = None
    validation: str = 'not_run'
    latency_ms: int = 0

class AnalystError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
