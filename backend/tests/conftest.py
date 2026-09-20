import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, build_engine, get_db
from app.main import app
from app.models.entities import Project, Site
from app.core.config import settings


@pytest.fixture
def db_factory(tmp_path, monkeypatch):
    engine = build_engine('sqlite:///' + (tmp_path / 'test.db').as_posix())
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        project = Project(name='Test Harbour', code='TEST', location='Demo')
        db.add(project)
        db.flush()
        db.add(Site(project_id=project.id, name='Tower A', zone='East'))
        db.commit()
    monkeypatch.setattr(settings, 'ai_provider', 'mock')
    monkeypatch.setattr(settings, 'upload_dir', tmp_path / 'uploads')
    yield factory
    engine.dispose()


@pytest.fixture
def client(db_factory):
    def override():
        with db_factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
    app.dependency_overrides[get_db] = override
    # Do not enter lifespan: fixture owns initialization of an isolated DB.
    test_client = TestClient(app, raise_server_exceptions=True)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def forbid_paid_http(monkeypatch):
    import httpx
    def blocked(*args, **kwargs):
        raise AssertionError('External HTTP forbidden in tests; inject a mocked SDK or MockTransport.')
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', blocked)

@pytest.fixture(autouse=True)
def isolate_workload_provider_defaults(monkeypatch):
    # Developer .env may select a live workload independently of legacy ai_provider.
    # Individual provider tests explicitly override these defaults when needed.
    monkeypatch.setattr(settings, 'vision_provider', None)
    monkeypatch.setattr(settings, 'reinspection_provider', None)
    monkeypatch.setattr(settings, 'reinspection_model', None)
    monkeypatch.setattr(settings, 'vision_prompt_version', 'vision-v1')
