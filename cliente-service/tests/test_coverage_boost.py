"""
Tests adicionales para alcanzar 80% de cobertura
Enfocados en las líneas específicas que faltan
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

class TestCoverageBoost:
    """Tests para completar la cobertura al 80%"""

    @pytest.mark.asyncio
    async def test_historico_endpoint_mock(self):
        """Test endpoint historico completo"""
        from httpx import AsyncClient
        from app.main import app
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
            estadisticas={
                "cliente_id": "CLI001", "total_compras": 0, "total_productos_unicos": 0,
                "total_devoluciones": 0, "valor_total_compras": 0.0, "promedio_orden": 0.0,
                "frecuencia_compra_mensual": 0.0, "tasa_devolucion": 0.0, "cliente_desde": None,
                "ultima_compra": None, "updated_at": None
            },
            metadatos={
                "consulta_took_ms": 25, "fecha_consulta": datetime.now().isoformat() + "Z",
                "limite_meses": 12, "vendedor_id": "VEN001", "incluyo_devoluciones": True,
                "cumple_sla": True, "total_items": {"compras": 0, "productos_preferidos": 0, "devoluciones": 0},
                "advertencias_performance": []
            }
        )
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_historico_completo.return_value = mock_historico
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/cliente/CLI001/historico",
                    params={"vendedor_id": "VEN001"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "cliente" in data
                assert "metadatos" in data

    @pytest.mark.asyncio
    async def test_service_obtener_metricas_detailed(self):
        """Test obtener métricas detallado"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository methods
        service.repository.contar_clientes = AsyncMock(return_value=20)
        service.repository.contar_clientes_activos = AsyncMock(return_value=18)
        service.repository.contar_consultas_hoy = AsyncMock(return_value=10)
        
        resultado = await service.obtener_metricas()
        
        assert resultado["service"] == "cliente-service"
        assert resultado["stats"]["total_clientes"] == 20
        assert resultado["stats"]["clientes_activos"] == 18
        assert resultado["stats"]["clientes_inactivos"] == 2
        assert resultado["stats"]["consultas_realizadas_hoy"] == 10
        assert "sla" in resultado
        assert "timestamp" in resultado

    @pytest.mark.asyncio
    async def test_service_listar_clientes_detailed(self):
        """Test listar clientes detallado"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository response
        mock_clientes = [
            {
                "id": "CLI001", "nit": "900123456-7", "nombre": "Cliente 1",
                "codigo_unico": "C001", "email": "cli1@test.com",
                "telefono": "+57-1-111", "direccion": "Dir 1",
                "ciudad": "Bogotá", "pais": "CO", "activo": True,
                "created_at": datetime.now(), "updated_at": datetime.now()
            },
            {
                "id": "CLI002", "nit": "800123456-2", "nombre": "Cliente 2",
                "codigo_unico": "C002", "email": "cli2@test.com",
                "telefono": "+57-1-222", "direccion": "Dir 2",
                "ciudad": "Medellín", "pais": "CO", "activo": True,
                "created_at": datetime.now(), "updated_at": datetime.now()
            }
        ]
        
        service.repository.listar_clientes = AsyncMock(return_value=mock_clientes)
        
        # Test con diferentes parámetros
        resultado = await service.listar_clientes(limite=10, offset=0, activos_solo=True)
        
        assert len(resultado) == 2
        assert resultado[0]["nombre"] == "Cliente 1"
        assert resultado[1]["nombre"] == "Cliente 2"

    @pytest.mark.asyncio
    async def test_routes_error_handling(self):
        """Test manejo de errores en routes"""
        from httpx import AsyncClient
        from app.main import app
        from fastapi import HTTPException
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            # Test error 500 en search
            mock_service = AsyncMock()
            mock_service.buscar_cliente.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/cliente/search",
                    params={"q": "test", "vendedor_id": "VEN001"}
                )
                
                assert response.status_code == 500
                data = response.json()
                assert "error" in data["detail"]
                assert "timestamp" in data["detail"]

    @pytest.mark.asyncio
    async def test_routes_search_not_found(self):
        """Test búsqueda cliente no encontrado"""
        from httpx import AsyncClient
        from app.main import app
        from fastapi import HTTPException
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.buscar_cliente.side_effect = HTTPException(
                status_code=404,
                detail={"error": "CLIENT_NOT_FOUND", "message": "No encontrado"}
            )
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/cliente/search",
                    params={"q": "NOEXISTE", "vendedor_id": "VEN001"}
                )
                
                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_routes_historico_error(self):
        """Test error en endpoint historico"""
        from httpx import AsyncClient
        from app.main import app
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_historico_completo.side_effect = Exception("Error interno")
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/cliente/CLI001/historico",
                    params={"vendedor_id": "VEN001"}
                )
                
                assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_routes_list_error(self):
        """Test error en endpoint listar"""
        from httpx import AsyncClient
        from app.main import app
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.listar_clientes.side_effect = Exception("DB connection failed")
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/cliente/")
                
                assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_service_database_error_handling(self):
        """Test manejo de errores de base de datos"""
        from app.services.client_service import ClienteService
        from fastapi import HTTPException
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock error de conexión de base de datos
        service.repository.buscar_cliente_por_termino = AsyncMock(side_effect=Exception("DB Connection failed"))
        service.repository.registrar_consulta = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.buscar_cliente("test", "VEN001")
        
        assert exc_info.value.status_code == 500
        assert "INTERNAL_SERVER_ERROR" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_with_pagination_params(self):
        """Test listado con parámetros de paginación"""
        from httpx import AsyncClient
        from app.main import app
        
        mock_clientes = [
            {
                "id": "CLI001", "nit": "900123456-7", "nombre": "Paginated Client",
                "codigo_unico": "PAG001", "email": "pag@test.com",
                "telefono": "+57-1-3333", "direccion": "Pag Street",
                "ciudad": "Cali", "pais": "CO", "activo": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.listar_clientes.return_value = mock_clientes
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/cliente/",
                    params={
                        "limite": 5,
                        "offset": 10,
                        "activos_solo": False,
                        "ordenar_por": "nit"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["nombre"] == "Paginated Client"

    @pytest.mark.asyncio
    async def test_historico_with_optional_params(self):
        """Test historico con parámetros opcionales"""
        from httpx import AsyncClient
        from app.main import app
        from app.schemas import HistoricoCompletoResponse, ClienteBasicoResponse
        
        mock_historico = HistoricoCompletoResponse(
            cliente=ClienteBasicoResponse(
                id="CLI001", nit="900123456-7", nombre="Test Params",
                codigo_unico="TPARAM", email="param@test.com",
                telefono="+57-1-4444", direccion="Param St",
                ciudad="Bucaramanga", pais="CO", activo=True,
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            historico_compras=[], productos_preferidos=[], devoluciones=[],
            estadisticas={
                "cliente_id": "CLI001", "total_compras": 5, "total_productos_unicos": 3,
                "total_devoluciones": 1, "valor_total_compras": 150.0, "promedio_orden": 30.0,
                "frecuencia_compra_mensual": 1.2, "tasa_devolucion": 0.1, "cliente_desde": None,
                "ultima_compra": None, "updated_at": None
            },
            metadatos={
                "consulta_took_ms": 45, "fecha_consulta": datetime.now().isoformat() + "Z",
                "limite_meses": 6, "vendedor_id": "VEN001", "incluyo_devoluciones": False,
                "cumple_sla": True, "total_items": {"compras": 5, "productos_preferidos": 3, "devoluciones": 1},
                "advertencias_performance": []
            }
        )
        
        with patch('app.routes.client.ClienteService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.obtener_historico_completo.return_value = mock_historico
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as client:
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
                assert data["cliente"]["nombre"] == "Test Params"
                assert data["metadatos"]["limite_meses"] == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])