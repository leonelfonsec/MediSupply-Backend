import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
import fakeredis.aioredis
import tempfile
import os
from app.main import app
from app.db import get_session, Base
from app.cache import get_redis
from app.config import Settings

# Test database URL using SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

@pytest.fixture
def test_settings():
    """Configuración de pruebas."""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/15",  # DB dedicada para tests
        api_prefix="/api",
        page_size_default=10,
        page_size_max=50
    )

@pytest.fixture
async def test_engine():
    """Engine de base de datos para pruebas."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Silenciar logs en pruebas
        poolclass=NullPool,  # Evitar problemas de conexión en SQLite
    )
    
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Limpiar después de las pruebas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """Sesión de base de datos para pruebas."""
    async_session = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
async def fake_redis():
    """Redis falso para pruebas."""
    fake_redis_instance = fakeredis.aioredis.FakeRedis(
        decode_responses=True,
        encoding="utf-8"
    )
    return fake_redis_instance

@pytest.fixture
def test_client(test_session, fake_redis):
    """Cliente de pruebas con dependencias mockeadas."""
    
    # Override dependencies
    app.dependency_overrides[get_session] = lambda: test_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    
    with TestClient(app) as client:
        yield client
    
    # Limpiar overrides
    app.dependency_overrides.clear()

@pytest.fixture
def mock_session():
    """Mock de sesión de base de datos."""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture  
def mock_redis():
    """Mock de Redis."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    return redis_mock

# Fixture de datos de prueba comunes
@pytest.fixture
def sample_producto_data():
    """Datos de ejemplo para producto."""
    return {
        "id": "TEST001",
        "codigo": "TST001",
        "nombre": "Producto de Prueba 500mg",
        "categoria_id": "TEST_CATEGORY",
        "presentacion": "Tableta",
        "precio_unitario": 1500.00,
        "requisitos_almacenamiento": "Temperatura ambiente",
        "activo": True
    }

@pytest.fixture
def sample_inventario_data():
    """Datos de ejemplo para inventario."""
    return {
        "id": 1,
        "producto_id": "TEST001",
        "pais": "CO",
        "bodega_id": "TEST_WAREHOUSE", 
        "lote": "TEST_LOTE_001",
        "cantidad": 500,
        "vence": "2025-12-31",
        "condiciones": "Almacén de pruebas"
    }

# Markers personalizados
pytestmark = pytest.mark.asyncio