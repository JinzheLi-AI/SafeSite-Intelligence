import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError
from app.core.config import settings
from app.ai.accounting import ensure_usage_columns
from app.core.jurisdictions import ensure_project_jurisdiction
from app.db.session import Base, engine, SessionLocal
from app.api import overview, inspections, incidents, uploads, knowledge, analyst
from app.seed.demo import seed_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    ensure_project_jurisdiction(engine)
    ensure_usage_columns(engine)
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_database(db)
    logger.info('SafeSite ready; provider=%s; automatic seed=%s', settings.ai_provider, settings.auto_seed)
    yield


app = FastAPI(title=settings.app_name, version='0.1.0', lifespan=lifespan,
    description='Human-controlled construction safety demo. AI findings and sample guidance are demonstration data.')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
    allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type', 'X-SafeSite-Language'])
for router in (overview.router, inspections.router, incidents.router, uploads.router, knowledge.router, analyst.router):
    app.include_router(router, prefix='/api/v1')
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=str(settings.upload_dir)), name='uploads')


@app.exception_handler(StaleDataError)
@app.exception_handler(IntegrityError)
async def conflict_handler(request: Request, exc: Exception):
    logger.warning('Concurrent or conflicting update: %s', type(exc).__name__)
    return JSONResponse(status_code=409, content={'detail': 'This record changed or the request conflicts with existing data. Refresh and retry.'})


@app.exception_handler(OperationalError)
async def database_handler(request: Request, exc: Exception):
    logger.exception('Database operation failed')
    return JSONResponse(status_code=503, content={'detail': 'Database temporarily unavailable. Please retry.'})
