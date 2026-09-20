from fastapi import APIRouter, Depends, Header
from typing import Annotated, Literal
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.analyst.contracts import AskRequest, AnalyticsAnswer
from app.analyst.metrics import METRICS
from app.analyst.service import SafetyAnalystService

router=APIRouter(prefix='/analyst',tags=['Safety analytics'])

@router.get('/capabilities')
def capabilities():
    from app.ai.capabilities import readiness
    configured=readiness(settings,'analyst')
    return {'provider':settings.analyst_provider,'configuration':configured,
        'model':settings.analyst_model if settings.analyst_provider in ('openai','deepseek') else None,
        'flexible_ready':settings.analyst_provider in ('openai','deepseek') and configured['ready'],
        'metrics':{k:v.definition for k,v in METRICS.items()},
        'timezone':'Asia/Hong_Kong (UTC+08:00)'}

@router.post('/query',response_model=AnalyticsAnswer)
def query(request: AskRequest, db: Session=Depends(get_db), language: Annotated[Literal['en','zh-CN'], Header(alias='X-SafeSite-Language')] = 'en'):
    # The session supplies only its configured engine. Execution opens a new read-only connection.
    return SafetyAnalystService(db.get_bind()).ask(request.question.strip(),request.language or language)
