"""
Tests adicionales para alcanzar 80% de cobertura
Enfoque en líneas específicas faltantes de client_service y client_repo
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

class TestCoverageCompleta:
    """Tests para completar cobertura específica"""

    @pytest.mark.asyncio
    async def test_service_buscar_cliente_auditoria_error_path(self):
        """Test path de error en auditoría durante búsqueda"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock cliente encontrado
        mock_cliente = MagicMock()
        mock_cliente.nit = "900123456-7"
        mock_cliente.nombre = "Test"
        mock_cliente.id = "CLI001"
        mock_cliente.codigo_unico = "TST001"
        mock_cliente.email = "test@test.com"
        mock_cliente.telefono = "+57-1-2345678"
        mock_cliente.direccion = "Calle Test"
        mock_cliente.ciudad = "Bogotá"
        mock_cliente.pais = "CO"
        mock_cliente.activo = True
        mock_cliente.created_at = datetime.now()
        mock_cliente.updated_at = datetime.now()
        
        service.repository.buscar_cliente_por_termino = AsyncMock(return_value=mock_cliente)
        
        # Mock auditoría que falla para cubrir except
        service._registrar_auditoria = AsyncMock(side_effect=Exception("Audit failed"))
        
        with patch('app.services.client_service.ClienteBasicoResponse') as mock_response_class:
            mock_response = MagicMock()
            mock_response.nit = "900123456-7" 
            mock_response_class.model_validate.return_value = mock_response
            
            # Debe continuar a pesar del error de auditoría
            resultado = await service.buscar_cliente("900123456-7", "VEN001")
            
            assert resultado.nit == "900123456-7"

    @pytest.mark.asyncio
    async def test_service_buscar_cliente_mapeo_manual_fallback(self):
        """Test fallback a mapeo manual cuando model_validate falla"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock cliente encontrado
        mock_cliente = MagicMock()
        mock_cliente.nit = "900123456-7"
        mock_cliente.nombre = "Test Manual"
        mock_cliente.id = "CLI002"
        mock_cliente.codigo_unico = "MAN001"
        mock_cliente.email = "manual@test.com"
        mock_cliente.telefono = "+57-1-1111"
        mock_cliente.direccion = "Manual St"
        mock_cliente.ciudad = "Cali"
        mock_cliente.pais = "CO"
        mock_cliente.activo = True
        mock_cliente.created_at = datetime.now()
        mock_cliente.updated_at = datetime.now()
        
        service.repository.buscar_cliente_por_termino = AsyncMock(return_value=mock_cliente)
        service._registrar_auditoria = AsyncMock()
        
        # Mock model_validate que falla para activar fallback manual
        with patch('app.services.client_service.ClienteBasicoResponse') as mock_response_class:
            # Primer intento falla
            mock_response_class.model_validate.side_effect = Exception("Validation failed")
            
            # Segundo intento (constructor directo) funciona
            mock_manual_response = MagicMock()
            mock_manual_response.nit = "900123456-7"
            mock_response_class.return_value = mock_manual_response
            
            resultado = await service.buscar_cliente("900123456-7", "VEN001")
            
            # Verificar que se usó el constructor directo
            mock_response_class.assert_called()

    @pytest.mark.asyncio
    async def test_service_obtener_metricas_error_handling(self):
        """Test manejo de errores en obtener métricas"""
        from app.services.client_service import ClienteService
        from fastapi import HTTPException
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository que falla
        service.repository.contar_clientes = AsyncMock(side_effect=Exception("DB Error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_metricas()
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_service_listar_clientes_error_handling(self):
        """Test manejo de errores en listar clientes"""
        from app.services.client_service import ClienteService
        from fastapi import HTTPException
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository que falla
        service.repository.listar_clientes = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(HTTPException) as exc_info:
            await service.listar_clientes()
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_repository_buscar_cliente_error_handling(self):
        """Test manejo de errores en repository buscar cliente"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Mock session.execute que falla
        repository.session.execute = AsyncMock(side_effect=Exception("Query failed"))
        
        # Debe retornar None en caso de error
        resultado = await repository.buscar_cliente_por_termino("test")
        assert resultado is None

    @pytest.mark.asyncio
    async def test_repository_listar_clientes_error_handling(self):
        """Test manejo de errores en repository listar clientes"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Mock session.execute que falla
        repository.session.execute = AsyncMock(side_effect=Exception("DB connection lost"))
        
        # Debe retornar lista vacía en caso de error
        resultado = await repository.listar_clientes()
        assert resultado == []

    @pytest.mark.asyncio
    async def test_repository_contar_clientes_error_handling(self):
        """Test manejo de errores en conteos"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Mock session.execute que falla
        repository.session.execute = AsyncMock(side_effect=Exception("Count query failed"))
        
        # Debe retornar 0 en caso de error
        total = await repository.contar_clientes()
        assert total == 0
        
        activos = await repository.contar_clientes_activos()
        assert activos == 0
        
        consultas = await repository.contar_consultas_hoy()
        assert consultas == 0

    @pytest.mark.asyncio
    async def test_repository_obtener_historico_error_handling(self):
        """Test manejo de errores en obtener histórico"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Mock session.execute que falla
        repository.session.execute = AsyncMock(side_effect=Exception("Complex query failed"))
        
        # Debe retornar None en caso de error
        resultado = await repository.obtener_historico_completo("CLI001", 12, True)
        assert resultado is None

    @pytest.mark.asyncio
    async def test_repository_registrar_consulta_error_paths(self):
        """Test diferentes paths de error en registrar consulta"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Test 1: Error al agregar a la sesión
        repository.session.add = MagicMock(side_effect=Exception("Add failed"))
        
        # No debe fallar, solo registrar el error internamente
        await repository.registrar_consulta("VEN001", "CLI001", "test", 100, {})
        
        # Test 2: Error al hacer commit
        repository.session.add = MagicMock()  # Resetear
        repository.session.commit = AsyncMock(side_effect=Exception("Commit failed"))
        
        # No debe fallar, solo registrar el error internamente
        await repository.registrar_consulta("VEN001", "CLI001", "test", 100, {})

    @pytest.mark.asyncio
    async def test_service_historico_completo_error_registrar_consulta(self):
        """Test error en registrar consulta durante histórico"""
        from app.services.client_service import ClienteService
        from fastapi import HTTPException
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository que retorna None para activar error 404
        service.repository.obtener_historico_completo = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_historico_completo("NOEXISTE", "VEN001")
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_service_historico_completo_con_error_general(self):
        """Test error general en histórico completo con registro de error"""
        from app.services.client_service import ClienteService
        from fastapi import HTTPException
        
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.sla_max_response_ms = 2000
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository que falla
        service.repository.obtener_historico_completo = AsyncMock(side_effect=Exception("Unexpected error"))
        service.repository.registrar_consulta = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_historico_completo("CLI001", "VEN001")
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_repository_buscar_cliente_diferentes_tipos_busqueda(self):
        """Test diferentes tipos de términos de búsqueda"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repository = ClienteRepository(mock_session)
        
        # Mock resultado exitoso
        mock_cliente = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_cliente
        mock_result.scalars.return_value = mock_scalars
        
        repository.session.execute = AsyncMock(return_value=mock_result)
        
        # Test búsqueda por NIT (solo números)
        resultado1 = await repository.buscar_cliente_por_termino("900123456")
        repository.session.execute.assert_called()
        
        # Test búsqueda por nombre (texto)
        resultado2 = await repository.buscar_cliente_por_termino("Farmacia Test")
        assert repository.session.execute.call_count >= 2
        
        # Test búsqueda por código (alfanumérico corto)
        resultado3 = await repository.buscar_cliente_por_termino("FSJ001")
        assert repository.session.execute.call_count >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])