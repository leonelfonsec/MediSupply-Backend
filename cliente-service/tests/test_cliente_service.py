"""
Tests para cliente-service - HU07: Consultar Cliente
"""
import pytest
import asyncio
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_session, Base
from app.models import Cliente, CompraHistorico, DevolucionHistorico
from app.schemas import ClienteBusquedaRequest, HistoricoClienteRequest


# Configuración de testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
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
        ciudad="Bogotá",
        pais="CO",
        activo=True
    )
    
    test_session.add(cliente)
    await test_session.commit()
    return cliente


@pytest.fixture
async def sample_compras(test_session, sample_cliente):
    """Compras de prueba"""
    compras = []
    
    # Crear compras de los últimos 6 meses
    for i in range(10):
        fecha_compra = date.today() - timedelta(days=i * 15)
        
        compra = CompraHistorico(
            id=f"COMP{i:03d}",
            cliente_id=sample_cliente.id,
            orden_id=f"ORD{i:03d}",
            producto_id=f"PROD{i % 3:03d}",  # 3 productos diferentes
            producto_nombre=f"Producto Test {i % 3}",
            categoria_producto="Medicamentos",
            cantidad=10 + i,
            precio_unitario=Decimal("100.50"),
            precio_total=Decimal("100.50") * (10 + i),
            fecha_compra=fecha_compra,
            estado_orden="completada"
        )
        
        compras.append(compra)
        test_session.add(compra)
    
    await test_session.commit()
    return compras


@pytest.fixture
async def sample_devoluciones(test_session, sample_cliente, sample_compras):
    """Devoluciones de prueba"""
    devoluciones = []
    
    for i in range(2):
        devolucion = DevolucionHistorico(
            id=f"DEV{i:03d}",
            cliente_id=sample_cliente.id,
            compra_id=sample_compras[i].id,
            compra_orden_id=sample_compras[i].orden_id,
            producto_id=sample_compras[i].producto_id,
            producto_nombre=sample_compras[i].producto_nombre,
            cantidad_devuelta=5,
            motivo=f"Motivo de devolución {i}",
            categoria_motivo="calidad",
            fecha_devolucion=date.today() - timedelta(days=i * 10),
            estado="procesada"
        )
        
        devoluciones.append(devolucion)
        test_session.add(devolucion)
    
    await test_session.commit()
    return devoluciones


# ==========================================
# TESTS DE BÚSQUEDA DE CLIENTE
# ==========================================

@pytest.mark.asyncio
class TestBusquedaCliente:
    """Tests para búsqueda de cliente (Criterio de aceptación 1)"""
    
    async def test_busqueda_por_nit_exitosa(self, client, sample_cliente):
        """Test: El vendedor puede buscar un cliente por NIT"""
        response = await client.get(
            "/api/v1/cliente/search",
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