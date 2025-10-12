"""
Tests de integración para app/routes/client.py
Cobertura completa de los endpoints REST
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import FastAPI
from datetime import datetime

from app.main import app
from app.routes.client import router


class TestClientRoutes:
    """Tests para los endpoints de cliente"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP de prueba"""
        return AsyncClient(app=app, base_url="http://test")
    
    @pytest.fixture
    def mock_service(self):
        """Mock del servicio de clientes"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_cliente_response(self):
        """Mock de respuesta de cliente"""
        from app.schemas import ClienteBasicoResponse
        return ClienteBasicoResponse(
            id="CLI001",
            nit="900123456-7",
            nombre="Farmacia Test",
            codigo_unico="FSJ001",
            email="test@test.com",
            telefono="+57-1-2345678",
            direccion="Calle 123",
            ciudad="Bogotá",
            pais="CO",
            activo=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test: Endpoint de health check"""
        with patch('app.routes.client.get_settings') as mock_settings:
            mock_config = MagicMock()
            mock_config.sla_max_response_ms = 2000
            mock_settings.return_value = mock_config
            
            async with client as ac:
                response = await ac.get("/api/cliente/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "cliente-service"
            assert "sla_max_response_ms" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        """Test: Endpoint de métricas"""
        mock_metrics = {
            "service": "cliente-service",
            "stats": {
                "total_clientes": 10,
                "clientes_activos": 8,
                "clientes_inactivos": 2,
                "consultas_realizadas_hoy": 5
            },
            "sla": {
                "max_response_time_ms": 2000
            }
        }
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_metricas.return_value = mock_metrics
            mock_service_class.return_value = mock_service
            
            response = await client.get("/api/cliente/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["stats"]["total_clientes"] == 10
            assert data["stats"]["clientes_activos"] == 8
            assert data["sla"]["max_response_time_ms"] == 2000

    @pytest.mark.asyncio
    async def test_search_cliente_success(self, client, mock_cliente_response):
        """Test: Búsqueda exitosa de cliente"""
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.buscar_cliente.return_value = mock_cliente_response
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/search",
                params={"q": "900123456-7", "vendedor_id": "VEN001"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["nit"] == "900123456-7"
            assert data["nombre"] == "Farmacia Test"
            assert data["codigo_unico"] == "FSJ001"

    @pytest.mark.asyncio
    async def test_search_cliente_missing_params(self, client):
        """Test: Búsqueda con parámetros faltantes"""
        # Falta vendedor_id
        response = await client.get(
            "/api/cliente/search",
            params={"q": "test"}
        )
        assert response.status_code == 422
        
        # Falta término de búsqueda
        response = await client.get(
            "/api/cliente/search",
            params={"vendedor_id": "VEN001"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_cliente_not_found(self, client):
        """Test: Cliente no encontrado"""
        from fastapi import HTTPException
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.buscar_cliente.side_effect = HTTPException(
                status_code=404,
                detail={
                    "error": "CLIENT_NOT_FOUND",
                    "message": "Cliente no encontrado"
                }
            )
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/search",
                params={"q": "NOEXISTE", "vendedor_id": "VEN001"}
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_cliente_server_error(self, client):
        """Test: Error interno del servidor"""
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.buscar_cliente.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/search", 
                params={"q": "test", "vendedor_id": "VEN001"}
            )
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_historico_success(self, client):
        """Test: Obtener histórico exitoso"""
        from app.schemas import HistoricoCompletoResponse, ClienteBasicoResponse
        
        mock_historico = HistoricoCompletoResponse(
            cliente=ClienteBasicoResponse(
                id="CLI001", nit="900123456-7", nombre="Test",
                codigo_unico="TST001", email="test@test.com",
                telefono="+57-1-2345678", direccion="Test St",
                ciudad="Bogotá", pais="CO", activo=True,
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            historico_compras=[],
            productos_preferidos=[],
            devoluciones=[],
            estadisticas={
                "cliente_id": "CLI001",
                "total_compras": 0,
                "total_productos_unicos": 0,
                "total_devoluciones": 0,
                "valor_total_compras": 0.0,
                "promedio_orden": 0.0,
                "frecuencia_compra_mensual": 0.0,
                "tasa_devolucion": 0.0,
                "cliente_desde": None,
                "ultima_compra": None,
                "updated_at": None
            },
            metadatos={
                "consulta_took_ms": 25,
                "fecha_consulta": datetime.now().isoformat() + "Z",
                "limite_meses": 12,
                "vendedor_id": "VEN001",
                "incluyo_devoluciones": True,
                "cumple_sla": True,
                "total_items": {"compras": 0, "productos_preferidos": 0, "devoluciones": 0},
                "advertencias_performance": []
            }
        )
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_historico_completo.return_value = mock_historico
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/CLI001/historico",
                params={"vendedor_id": "VEN001"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "cliente" in data
            assert "historico_compras" in data
            assert "productos_preferidos" in data
            assert "devoluciones" in data
            assert "estadisticas" in data
            assert "metadatos" in data
            assert data["metadatos"]["cumple_sla"] is True

    @pytest.mark.asyncio
    async def test_get_historico_with_params(self, client):
        """Test: Historico con parámetros opcionales"""
        from app.schemas import HistoricoCompletoResponse, ClienteBasicoResponse
        
        mock_historico = HistoricoCompletoResponse(
            cliente=ClienteBasicoResponse(
                id="CLI001", nit="900123456-7", nombre="Test",
                codigo_unico="TST001", email="test@test.com",
                telefono="+57-1-2345678", direccion="Test St",
                ciudad="Bogotá", pais="CO", activo=True,
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            historico_compras=[], productos_preferidos=[], devoluciones=[],
            estadisticas={"cliente_id": "CLI001", "total_compras": 0, "total_productos_unicos": 0,
                         "total_devoluciones": 0, "valor_total_compras": 0.0, "promedio_orden": 0.0,
                         "frecuencia_compra_mensual": 0.0, "tasa_devolucion": 0.0, "cliente_desde": None,
                         "ultima_compra": None, "updated_at": None},
            metadatos={"consulta_took_ms": 25, "fecha_consulta": datetime.now().isoformat() + "Z",
                      "limite_meses": 6, "vendedor_id": "VEN001", "incluyo_devoluciones": False,
                      "cumple_sla": True, "total_items": {"compras": 0, "productos_preferidos": 0, "devoluciones": 0},
                      "advertencias_performance": []}
        )
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_historico_completo.return_value = mock_historico
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/CLI001/historico",
                params={
                    "vendedor_id": "VEN001",
                    "limite_meses": 6,
                    "incluir_devoluciones": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["metadatos"]["limite_meses"] == 6
            assert data["metadatos"]["incluyo_devoluciones"] is False

    @pytest.mark.asyncio
    async def test_list_clientes_success(self, client):
        """Test: Listar clientes exitoso"""
        mock_clientes = [
            {
                "id": "CLI001", "nit": "900123456-7", "nombre": "Farmacia Test 1",
                "codigo_unico": "FSJ001", "email": "test1@test.com",
                "telefono": "+57-1-2345678", "direccion": "Calle 123",
                "ciudad": "Bogotá", "pais": "CO", "activo": True,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
            },
            {
                "id": "CLI002", "nit": "800987654-3", "nombre": "Farmacia Test 2", 
                "codigo_unico": "FSJ002", "email": "test2@test.com",
                "telefono": "+57-2-9876543", "direccion": "Carrera 456",
                "ciudad": "Medellín", "pais": "CO", "activo": True,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
            }
        ]
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.listar_clientes.return_value = mock_clientes
            mock_service_class.return_value = mock_service
            
            response = await client.get("/api/cliente/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["nombre"] == "Farmacia Test 1"

    @pytest.mark.asyncio
    async def test_list_clientes_with_pagination(self, client):
        """Test: Listar clientes con paginación"""
        mock_clientes = [
            {
                "id": "CLI001", "nit": "900123456-7", "nombre": "Farmacia Test",
                "codigo_unico": "FSJ001", "email": "test@test.com",
                "telefono": "+57-1-2345678", "direccion": "Calle 123",
                "ciudad": "Bogotá", "pais": "CO", "activo": True,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
            }
        ]
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.listar_clientes.return_value = mock_clientes
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/",
                params={"limite": 1, "offset": 0, "ordenar_por": "nombre"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 1

    @pytest.mark.asyncio
    async def test_list_clientes_include_inactive(self, client):
        """Test: Listar clientes incluyendo inactivos"""
        mock_clientes = [
            {
                "id": "CLI001", "nit": "900123456-7", "nombre": "Cliente Activo",
                "codigo_unico": "ACT001", "email": "activo@test.com", 
                "telefono": "+57-1-2345678", "direccion": "Calle 123",
                "ciudad": "Bogotá", "pais": "CO", "activo": True,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
            },
            {
                "id": "CLI002", "nit": "800987654-3", "nombre": "Cliente Inactivo",
                "codigo_unico": "INA001", "email": "inactivo@test.com",
                "telefono": "+57-2-9876543", "direccion": "Carrera 456", 
                "ciudad": "Medellín", "pais": "CO", "activo": False,
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
            }
        ]
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.listar_clientes.return_value = mock_clientes
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/",
                params={"activos_solo": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            activos = [c for c in data if c["activo"]]
            inactivos = [c for c in data if not c["activo"]]
            assert len(activos) == 1
            assert len(inactivos) == 1

    @pytest.mark.asyncio
    async def test_endpoint_performance_sla(self, client):
        """Test: Performance de endpoints cumple SLA"""
        with patch('app.routes.client.get_settings') as mock_settings:
            mock_config = MagicMock()
            mock_config.sla_max_response_ms = 2000
            mock_settings.return_value = mock_config
            
            start_time = time.perf_counter()
            
            response = await client.get("/api/cliente/health")
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            assert response.status_code == 200
            assert elapsed_ms < 2000  # Debe cumplir SLA

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, client):
        """Test: Manejo consistente de errores"""
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.buscar_cliente.side_effect = Exception("Internal error")
            mock_service_class.return_value = mock_service
            
            response = await client.get(
                "/api/cliente/search",
                params={"q": "test", "vendedor_id": "VEN001"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
            assert "message" in data["detail"]
            assert "timestamp" in data["detail"]

    @pytest.mark.asyncio
    async def test_validation_errors(self, client):
        """Test: Errores de validación de parámetros"""
        # Término de búsqueda muy corto
        response = await client.get(
            "/api/cliente/search",
            params={"q": "a", "vendedor_id": "VEN001"}
        )
        assert response.status_code == 422
        
        # Límite muy alto
        response = await client.get(
            "/api/cliente/",
            params={"limite": 1000}  # Max es 500
        )
        assert response.status_code == 422
        
        # Offset negativo
        response = await client.get(
            "/api/cliente/",
            params={"offset": -1}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])