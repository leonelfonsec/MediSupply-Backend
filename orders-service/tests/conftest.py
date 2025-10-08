import pytest
from fastapi.testclient import TestClient

# --- App FastAPI ---
from app.main import app as fastapi_app

# Si tu código usa Depends(get_session) para DB:
# ajusta estos imports a tus nombres reales
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base  # tu declarative base
from app.db import get_session  # tu dependencia de Session

# --- Cliente HTTP síncrono (vale para la mayoría de endpoints) ---
@pytest.fixture()
def client():
    return TestClient(fastapi_app)

# --- DB SQLite en memoria y override de dependencia ---
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as s:
        yield s
        await s.rollback()

@pytest.fixture(autouse=True)
def override_db(test_session):
    async def _override():
        yield test_session
    fastapi_app.dependency_overrides[get_session] = _override
    yield
    fastapi_app.dependency_overrides.clear()

# --- Redis falso (si usas redis.Redis en tu código) ---
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis
    import redis
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis, "Redis", lambda *a, **k: r)
    return r

# --- Celery en modo eager (las tareas se ejecutan al instante) ---
@pytest.fixture(autouse=True)
def celery_eager(monkeypatch):
    try:
        from app.celery_worker import celery_app
        celery_app.conf.task_always_eager = True
        celery_app.conf.task_eager_propagates = True
    except Exception:
        pass
