# tests/conftest.py
import importlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.db import get_session
from app.models import Base

# -----------------------------
# TestClient con lifespan real
# -----------------------------
@pytest.fixture()
def client(test_engine, monkeypatch):
    """
    TestClient con lifespan + engine parcheado a SQLite en memoria.
    Evita conexiones a Postgres durante el on_startup.
    """
    import app.main as main_mod
    import app.db as db_mod

    # Parchar ambos módulos a usar el engine de pruebas
    monkeypatch.setattr(main_mod, "engine", test_engine, raising=True)
    monkeypatch.setattr(db_mod, "engine", test_engine, raising=True)

    # Lifespan activo para que cuenten líneas de startup/shutdown en cobertura
    with TestClient(fastapi_app) as c:
        yield c
# -----------------------------
# Engine SQLite en memoria
# -----------------------------
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()

# -----------------------------
# Sesión para PRE-SEMBRAR datos
# -----------------------------
@pytest.fixture
async def test_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s:
        try:
            yield s
        finally:
            await s.rollback()

# -----------------------------
# OVERRIDE por REQUEST (clave)
#   - Crea una AsyncSession NUEVA por request del cliente
#   - No reutiliza test_session
# -----------------------------
@pytest.fixture(autouse=True)
def override_db(test_engine, monkeypatch):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async def _override():
        async with Session() as s:
            yield s

    # FastAPI Depends(...)
    fastapi_app.dependency_overrides[get_session] = _override

    # Si algún módulo importa app.db.get_session directamente, lo forzamos también
    dbmod = importlib.import_module("app.db")
    monkeypatch.setattr(dbmod, "get_session", _override)

    yield
    fastapi_app.dependency_overrides.clear()

# -----------------------------
# Redis falso
# -----------------------------
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis, redis
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis, "Redis", lambda *a, **k: r)
    return r

# -----------------------------
# Celery dummy (evita kombu/redis reales)
# -----------------------------
@pytest.fixture(autouse=True)
def _replace_celery_object(monkeypatch):
    main = importlib.import_module("app.main")

    class _DummyCelery:
        def __init__(self):
            self.calls = []
        def send_task(self, name, args=None, kwargs=None, **kw):
            self.calls.append((name, args, kwargs))
            return None

    monkeypatch.setattr(main, "celery", _DummyCelery())
