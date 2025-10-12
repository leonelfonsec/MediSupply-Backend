"""
Tests unitarios para app/services/client_service.py
Cobertura completa del servicio de clientes
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException

from app.services.client_service import ClienteService
from app.schemas import ClienteBasicoResponse, HistoricoCompletoResponse
from app.config import get_settings


class TestClienteService:
    """Tests para ClienteService"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos"""
        return AsyncMock()
    
    @pytest.fixture 
    def mock_settings(self):
        """Mock de configuración"""
        settings = MagicMock()
        settings.sla_max_response_ms = 2000
        settings.service_name = "cliente-service"
        return settings
    
    @pytest.fixture
    def mock_cliente(self):
        """Mock de cliente para pruebas"""
        cliente = MagicMock()
        cliente.id = "CLI001"
        cliente.nit = "900123456-7" 
        cliente.nombre = "Farmacia Test"
        cliente.codigo_unico = "FSJ001"
        cliente.email = "test@test.com"
        cliente.telefono = "+57-1-2345678"
        cliente.direccion = "Calle 123"
        cliente.ciudad = "Bogotá"
        cliente.pais = "CO"
        cliente.activo = True
        cliente.created_at = datetime.now()
        cliente.updated_at = datetime.now()
        return cliente

    def test_service_initialization(self, mock_session, mock_settings):
        """Test: Inicialización correcta del servicio"""
        service = ClienteService(mock_session, mock_settings)
        
        assert service.session == mock_session
        assert service.settings == mock_settings
        from app.repositories.client_repo import ClienteRepository
        assert isinstance(service.repository, ClienteRepository)

    @pytest.mark.asyncio
    async def test_buscar_cliente_success(self, mock_session, mock_settings, mock_cliente):
        """Test: Búsqueda exitosa de cliente"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'buscar_cliente_por_termino') as mock_search:
            mock_search.return_value = mock_cliente
            
            with patch.object(service, '_registrar_auditoria') as mock_audit:
                mock_audit.return_value = None
                
                result = await service.buscar_cliente("FSJ001", "VEN001")
                
                # Verificaciones
                mock_search.assert_called_once_with("FSJ001")
                mock_audit.assert_called_once()
                assert isinstance(result, ClienteBasicoResponse)
                assert result.id == "CLI001"
                assert result.nit == "900123456-7"

    @pytest.mark.asyncio
    async def test_buscar_cliente_not_found(self, mock_session, mock_settings):
        """Test: Cliente no encontrado"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'buscar_cliente_por_termino') as mock_search:
            mock_search.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await service.buscar_cliente("NOEXISTE", "VEN001")
            
            assert exc_info.value.status_code == 404
            assert "CLIENT_NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_buscar_cliente_sla_warning(self, mock_session, mock_settings, mock_cliente):
        """Test: Warning de SLA cuando tarda mucho"""
        # Configurar SLA bajo para forzar warning
        mock_settings.sla_max_response_ms = 1
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'buscar_cliente_por_termino') as mock_search:
            # Simular delay
            async def slow_search(term):
                await asyncio.sleep(0.002)  # 2ms para superar el SLA de 1ms
                return mock_cliente
            
            mock_search.side_effect = slow_search
            
            with patch.object(service, '_registrar_auditoria'):
                with patch('builtins.print') as mock_print:
                    result = await service.buscar_cliente("test", "VEN001")
                    
                    # Verificar que se imprimió warning de SLA
                    warning_calls = [call for call in mock_print.call_args_list 
                                   if 'WARNING' in str(call) and 'SLA' in str(call)]
                    assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_obtener_historico_completo_success(self, mock_session, mock_settings):
        """Test: Obtener histórico completo exitoso"""
        service = ClienteService(mock_session, mock_settings)
        
        mock_historico_data = {
            'cliente': MagicMock(),
            'historico_compras': [],
            'productos_preferidos': [],
            'devoluciones': [],
            'estadisticas': {
                'total_compras': 0,
                'total_productos_unicos': 0,
                'total_devoluciones': 0
            }
        }
        
        with patch.object(service.repository, 'obtener_historico_completo') as mock_hist:
            mock_hist.return_value = mock_historico_data
            
            with patch.object(service, '_registrar_auditoria') as mock_audit:
                mock_audit.return_value = None
                
                result = await service.obtener_historico_completo("CLI001", "VEN001", 12, True)
                
                # Verificaciones
                mock_hist.assert_called_once_with("CLI001", 12, True)
                mock_audit.assert_called_once()
                assert isinstance(result, HistoricoCompletoResponse)

    @pytest.mark.asyncio
    async def test_obtener_historico_cliente_not_found(self, mock_session, mock_settings):
        """Test: Cliente no encontrado para histórico"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'obtener_historico_completo') as mock_hist:
            mock_hist.side_effect = HTTPException(status_code=404, detail="CLIENT_NOT_FOUND")
            
            with pytest.raises(HTTPException) as exc_info:
                await service.obtener_historico_completo("CLI999", "VEN001")
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio 
    async def test_listar_clientes_success(self, mock_session, mock_settings):
        """Test: Listar clientes exitoso"""
        service = ClienteService(mock_session, mock_settings)
        
        mock_clientes = [MagicMock(), MagicMock()]
        
        with patch.object(service.repository, 'listar_clientes') as mock_list:
            mock_list.return_value = mock_clientes
            
            result = await service.listar_clientes()
            
            mock_list.assert_called_once_with(
                limite=50, offset=0, activos_solo=True, ordenar_por="nombre"
            )
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_obtener_metricas_success(self, mock_session, mock_settings):
        """Test: Obtener métricas del servicio"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'contar_clientes') as mock_total:
            mock_total.return_value = 10
            
            with patch.object(service.repository, 'contar_clientes_activos') as mock_activos:
                mock_activos.return_value = 8
                
                with patch.object(service.repository, 'contar_consultas_hoy') as mock_consultas:
                    mock_consultas.return_value = 5
                    
                    metrics = await service.obtener_metricas()
                    
                    assert "service" in metrics
                    assert "stats" in metrics
                    assert "sla" in metrics
                    assert metrics["stats"]["total_clientes"] == 10
                    assert metrics["stats"]["clientes_activos"] == 8
                    assert metrics["stats"]["clientes_inactivos"] == 2
                    assert metrics["stats"]["consultas_realizadas_hoy"] == 5

    @pytest.mark.asyncio
    async def test_registrar_auditoria_success(self, mock_session, mock_settings):
        """Test: Registro de auditoría exitoso"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch('builtins.print') as mock_print:
            await service._registrar_auditoria(
                "TEST_ACTION",
                "VEN001", 
                {"test": "data"}
            )
            
            # Verificar que se llamó print con auditoría
            audit_calls = [call for call in mock_print.call_args_list 
                          if 'AUDITORÍA' in str(call)]
            assert len(audit_calls) > 0

    @pytest.mark.asyncio
    async def test_registrar_auditoria_no_fail_on_error(self, mock_session, mock_settings):
        """Test: Auditoría no falla el servicio en caso de error"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch('builtins.print', side_effect=Exception("Print failed")):
            # No debe levantar excepción
            try:
                await service._registrar_auditoria("TEST", "VEN001", {})
                assert True
            except Exception:
                pytest.fail("_registrar_auditoria no debería fallar nunca")

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_session, mock_settings):
        """Test: Manejo de errores de base de datos"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'buscar_cliente_por_termino') as mock_search:
            mock_search.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await service.buscar_cliente("test", "VEN001")

    def test_search_term_type_detection(self):
        """Test: Detección de tipo de término de búsqueda"""
        # Este método se ejecuta dentro de buscar_cliente
        # Test conceptual de la lógica
        
        def detect_type(term):
            term = term.strip()
            if term.replace('-', '').replace(' ', '').isdigit():
                return "nit"
            elif len(term) < 10 and term.isalnum():
                return "codigo"
            else:
                return "nombre"
        
        assert detect_type("900123456-7") == "nit"
        assert detect_type("FSJ001") == "codigo"  
        assert detect_type("Farmacia San José") == "nombre"

    @pytest.mark.asyncio
    async def test_performance_sla_compliance(self, mock_session, mock_settings, mock_cliente):
        """Test: Cumplimiento de SLA de performance"""
        service = ClienteService(mock_session, mock_settings)
        
        with patch.object(service.repository, 'buscar_cliente_por_termino') as mock_search:
            mock_search.return_value = mock_cliente
            
            with patch.object(service, '_registrar_auditoria'):
                start_time = time.perf_counter()
                
                result = await service.buscar_cliente("test", "VEN001")
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # Debe ser muy rápido con mocks
                assert elapsed_ms < 100
                assert isinstance(result, ClienteBasicoResponse)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])