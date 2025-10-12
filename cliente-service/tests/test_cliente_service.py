"""
Tests para cliente-service - HU07: Consultar Cliente
Tests completos con cobertura del 80%
"""
import pytest
import asyncio
import time
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from app.main import app
from app.db import get_session, Base
from app.models.client_model import Cliente
from app.schemas import ClienteBusquedaRequest, HistoricoClienteRequest
from app.services.client_service import ClienteService
from app.repositories.client_repo import ClienteRepository
from app.config import Settings

# Configuración de testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_cliente.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def test_session():
    """Sesión de base de datos para testing"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSession() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(test_session):
    """Cliente HTTP para testing"""
    def override_get_session():
        return test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_cliente(test_session):
    """Cliente de prueba"""
    cliente = Cliente(
        id="CLI001",
        nit="900123456-7",
        nombre="Farmacia San José",
        codigo_unico="FSJ001",
        email="contacto@farmaciasanjose.com",
        telefono="+57-1-2345678",
        direccion="Calle 45 #12-34",
        ciudad="Bogotá",
        pais="CO",
        activo=True
    )
    
    test_session.add(cliente)
    await test_session.commit()
    return cliente


# Mock fixtures for testing (simplified for current implementation)

@pytest.fixture
def sample_historico_data():
    """Datos de histórico simulados para testing"""
    return {
        'historico_compras': [],
        'productos_preferidos': [],
        'devoluciones': [],
        'estadisticas': {
            'total_compras': 0,
            'total_productos_unicos': 0, 
            'total_devoluciones': 0,
            'valor_total_compras': 0.0,
            'promedio_orden': 0.0,
            'frecuencia_compra_mensual': 0.0,
            'tasa_devolucion': 0.0
        }
    }


# ==========================================
# TESTS DE BÚSQUEDA DE CLIENTE
# ==========================================

@pytest.mark.asyncio
class TestBusquedaCliente:
    """Tests para búsqueda de cliente (Criterio de aceptación 1)"""
    
    async def test_busqueda_por_nit_exitosa(self, client, sample_cliente):
        """Test: El vendedor puede buscar un cliente por NIT"""
        response = await client.get(
            "/api/cliente/search",
            params={
                "q": "900123456-7",
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["nit"] == "900123456-7"
        assert data["nombre"] == "Farmacia San José"
        assert data["codigo_unico"] == "FSJ001"
        assert data["activo"] is True
    
    async def test_busqueda_por_nombre_exitosa(self, client, sample_cliente):
        """Test: El vendedor puede buscar un cliente por nombre"""
        response = await client.get(
            "/api/v1/cliente/search", 
            params={
                "q": "Farmacia San José",
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Farmacia San José"
    
    async def test_busqueda_por_codigo_unico_exitosa(self, client, sample_cliente):
        """Test: El vendedor puede buscar un cliente por código único"""
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "FSJ001", 
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["codigo_unico"] == "FSJ001"
    
    async def test_busqueda_cliente_no_encontrado(self, client):
        """Test: Cliente no encontrado"""
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "999999999-9",
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "CLIENT_NOT_FOUND"
    
    async def test_busqueda_performance_sla(self, client, sample_cliente):
        """Test: La consulta debe responder en ≤ 2 segundos"""
        start_time = time.perf_counter()
        
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "900123456-7",
                "vendedor_id": "VEN001"
            }
        )
        
        elapsed_time = (time.perf_counter() - start_time) * 1000  # ms
        
        assert response.status_code == 200
        assert elapsed_time <= 2000  # ≤ 2 segundos
        
        # Verificar headers de performance
        assert "X-Process-Time-Ms" in response.headers
        assert response.headers["X-SLA-Compliant"] == "True"


# ==========================================
# TESTS DE HISTÓRICO COMPLETO
# ==========================================

@pytest.mark.asyncio
class TestHistoricoCompleto:
    """Tests para histórico completo del cliente"""
    
    async def test_historico_completo_exitoso(self, client, sample_cliente, sample_compras, sample_devoluciones):
        """Test: El sistema muestra el histórico completo del cliente"""
        response = await client.get(
            f"/api/v1/cliente/{sample_cliente.id}/historico",
            params={
                "vendedor_id": "VEN001",
                "limite_meses": 12,
                "incluir_devoluciones": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "cliente" in data
        assert "historico_compras" in data
        assert "productos_preferidos" in data
        assert "devoluciones" in data
        assert "estadisticas" in data
        assert "metadatos" in data
        
        # Verificar datos del cliente
        assert data["cliente"]["nit"] == "900123456-7"
        assert data["cliente"]["nombre"] == "Farmacia San José"
        
        # Verificar histórico de compras (Criterio 2)
        assert len(data["historico_compras"]) > 0
        compra = data["historico_compras"][0]
        assert "orden_id" in compra
        assert "producto_nombre" in compra
        assert "cantidad" in compra
        assert "fecha_compra" in compra
        
        # Verificar productos preferidos (Criterio 3)
        assert len(data["productos_preferidos"]) > 0
        preferido = data["productos_preferidos"][0]
        assert "frecuencia_compra" in preferido
        assert preferido["frecuencia_compra"] > 0
        
        # Verificar devoluciones (Criterio 4)
        assert len(data["devoluciones"]) > 0
        devolucion = data["devoluciones"][0]
        assert "motivo" in devolucion
        assert "fecha_devolucion" in devolucion
        
        # Verificar estadísticas
        stats = data["estadisticas"]
        assert stats["total_compras"] > 0
        assert stats["total_productos_unicos"] > 0
        assert stats["total_devoluciones"] > 0
    
    async def test_historico_performance_sla(self, client, sample_cliente, sample_compras, sample_devoluciones):
        """Test: La consulta de histórico debe responder en ≤ 2 segundos"""
        start_time = time.perf_counter()
        
        response = await client.get(
            f"/api/v1/cliente/{sample_cliente.id}/historico",
            params={
                "vendedor_id": "VEN001"
            }
        )
        
        elapsed_time = (time.perf_counter() - start_time) * 1000  # ms
        
        assert response.status_code == 200
        assert elapsed_time <= 2000  # ≤ 2 segundos
        
        # Verificar metadatos de performance
        data = response.json()
        assert data["metadatos"]["cumple_sla"] is True
        assert data["metadatos"]["consulta_took_ms"] <= 2000
    
    async def test_historico_cliente_no_encontrado(self, client):
        """Test: Cliente no encontrado para histórico"""
        response = await client.get(
            "/api/v1/cliente/CLI999/historico",
            params={
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "CLIENT_NOT_FOUND"


# ==========================================
# TESTS DE TRAZABILIDAD
# ==========================================

@pytest.mark.asyncio
class TestTrazabilidad:
    """Tests para trazabilidad de consultas (Criterio 6)"""
    
    async def test_consulta_registrada_en_auditoria(self, client, sample_cliente, test_session):
        """Test: La información consultada queda registrada para trazabilidad"""
        # Realizar consulta
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "900123456-7",
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 200
        
        # Verificar que se registró en auditoría
        from app.models import ConsultaClienteLog
        from sqlalchemy import select
        
        stmt = select(ConsultaClienteLog).where(
            ConsultaClienteLog.vendedor_id == "VEN001",
            ConsultaClienteLog.cliente_id == sample_cliente.id
        )
        
        result = await test_session.execute(stmt)
        log_entry = result.scalar_one_or_none()
        
        assert log_entry is not None
        assert log_entry.tipo_consulta == "busqueda_cliente"
        assert log_entry.termino_busqueda == "900123456-7"
        assert log_entry.took_ms > 0


# ==========================================
# TESTS DE VALIDACIÓN DE DATOS
# ==========================================

@pytest.mark.asyncio
class TestValidacionDatos:
    """Tests para validación de datos de entrada"""
    
    async def test_validacion_termino_busqueda_vacio(self, client):
        """Test: Validación de término de búsqueda vacío"""
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "",
                "vendedor_id": "VEN001"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_validacion_vendedor_id_requerido(self, client):
        """Test: Validación de vendedor_id requerido"""
        response = await client.get(
            "/api/v1/cliente/search",
            params={
                "q": "900123456-7"
                # vendedor_id faltante
            }
        )
        
        assert response.status_code == 422  # Validation error


# ==========================================
# TESTS DE HEALTH CHECK
# ==========================================

@pytest.mark.asyncio
class TestHealthCheck:
    """Tests para health check del servicio"""
    
    async def test_health_check_simple(self, client):
        """Test: Health check simple"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_health_check_completo(self, client):
        """Test: Health check completo"""
        response = await client.get("/api/v1/cliente/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cliente-service"
        assert "sla_max_response_ms" in data