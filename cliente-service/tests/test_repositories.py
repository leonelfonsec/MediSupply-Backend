"""
Tests unitarios para app/repositories/client_repo.py
Cobertura completa del repositorio de clientes
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.client_repo import ClienteRepository


class TestClienteRepository:
    """Tests para ClienteRepository"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_cliente_row(self):
        """Mock de fila de cliente de BD"""
        row = MagicMock()
        row.id = "CLI001"
        row.nit = "900123456-7"
        row.nombre = "Farmacia Test"
        row.codigo_unico = "FSJ001"
        row.email = "test@test.com"
        row.telefono = "+57-1-2345678"
        row.direccion = "Calle 123"
        row.ciudad = "Bogotá"
        row.pais = "CO"
        row.activo = True
        row.created_at = datetime.now()
        row.updated_at = datetime.now()
        return row

    def test_repository_initialization(self, mock_session):
        """Test: Inicialización del repository"""
        repo = ClienteRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_termino_success_nit(self, mock_session, mock_cliente_row):
        """Test: Búsqueda exitosa por NIT"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cliente_row
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.buscar_cliente_por_termino("900123456-7")
        
        assert resultado == mock_cliente_row
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_termino_success_nombre(self, mock_session, mock_cliente_row):
        """Test: Búsqueda exitosa por nombre"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cliente_row
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.buscar_cliente_por_termino("Farmacia")
        
        assert resultado == mock_cliente_row
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_termino_success_codigo(self, mock_session, mock_cliente_row):
        """Test: Búsqueda exitosa por código único"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cliente_row
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.buscar_cliente_por_termino("FSJ001")
        
        assert resultado == mock_cliente_row
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_termino_not_found(self, mock_session):
        """Test: Cliente no encontrado"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.buscar_cliente_por_termino("NOEXISTE")
        
        assert resultado is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_listar_clientes_default(self, mock_session):
        """Test: Listado de clientes con parámetros por defecto"""
        repo = ClienteRepository(mock_session)
        
        mock_clientes = [MagicMock(), MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_clientes
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.listar_clientes()
        
        assert len(resultado) == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_listar_clientes_with_params(self, mock_session):
        """Test: Listado de clientes con parámetros específicos"""
        repo = ClienteRepository(mock_session)
        
        mock_clientes = [MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_clientes
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.listar_clientes(
            limite=10, 
            offset=5, 
            activos_solo=False, 
            ordenar_por="nit"
        )
        
        assert len(resultado) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_listar_clientes_solo_activos(self, mock_session):
        """Test: Listado de solo clientes activos"""
        repo = ClienteRepository(mock_session)
        
        mock_clientes = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_clientes
        mock_session.execute.return_value = mock_result
        
        resultado = await repo.listar_clientes(activos_solo=True)
        
        assert len(resultado) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_contar_clientes(self, mock_session):
        """Test: Contar total de clientes"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        mock_session.execute.return_value = mock_result
        
        total = await repo.contar_clientes()
        
        assert total == 15
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_contar_clientes_activos(self, mock_session):
        """Test: Contar clientes activos"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 12
        mock_session.execute.return_value = mock_result
        
        activos = await repo.contar_clientes_activos()
        
        assert activos == 12
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_contar_consultas_hoy(self, mock_session):
        """Test: Contar consultas realizadas hoy"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result
        
        consultas = await repo.contar_consultas_hoy()
        
        assert consultas == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_historico_completo_success(self, mock_session, mock_cliente_row):
        """Test: Obtener histórico completo exitoso"""
        repo = ClienteRepository(mock_session)
        
        # Mock para verificar que cliente existe
        mock_result_cliente = MagicMock()
        mock_result_cliente.scalar_one_or_none.return_value = mock_cliente_row
        
        # Mock para las consultas de histórico (vacías para simplicidad)
        mock_result_empty = MagicMock()
        mock_result_empty.fetchall.return_value = []
        mock_result_empty.scalars.return_value.all.return_value = []
        
        # Configurar múltiples llamadas a execute
        mock_session.execute.side_effect = [
            mock_result_cliente,  # Verificar cliente existe
            mock_result_empty,    # Compras
            mock_result_empty,    # Productos preferidos  
            mock_result_empty,    # Devoluciones
        ]
        
        resultado = await repo.obtener_historico_completo("CLI001", 12, True)
        
        assert "cliente" in resultado
        assert "historico_compras" in resultado
        assert "productos_preferidos" in resultado
        assert "devoluciones" in resultado
        assert "estadisticas" in resultado
        
        assert resultado["cliente"] == mock_cliente_row
        assert len(resultado["historico_compras"]) == 0
        assert len(resultado["productos_preferidos"]) == 0
        assert len(resultado["devoluciones"]) == 0

    @pytest.mark.asyncio 
    async def test_obtener_historico_completo_cliente_not_found(self, mock_session):
        """Test: Cliente no encontrado para histórico"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await repo.obtener_historico_completo("CLI999", 12, True)
        
        assert exc_info.value.status_code == 404
        assert "CLIENT_NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_session):
        """Test: Manejo de errores de base de datos"""
        repo = ClienteRepository(mock_session)
        
        mock_session.execute.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await repo.buscar_cliente_por_termino("test")
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_construction_with_different_terms(self, mock_session, mock_cliente_row):
        """Test: Construcción de queries con diferentes tipos de términos"""
        repo = ClienteRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cliente_row
        mock_session.execute.return_value = mock_result
        
        # Test con diferentes tipos de términos
        test_terms = [
            "900123456-7",  # NIT
            "FSJ001",       # Código  
            "Farmacia",     # Nombre
            "12345",        # Número
            "Test Corp"     # Nombre con espacio
        ]
        
        for term in test_terms:
            resultado = await repo.buscar_cliente_por_termino(term)
            assert resultado == mock_cliente_row
        
        # Verificar que se ejecutaron todas las consultas
        assert mock_session.execute.call_count == len(test_terms)

    @pytest.mark.asyncio
    async def test_pagination_and_sorting(self, mock_session):
        """Test: Paginación y ordenamiento"""
        repo = ClienteRepository(mock_session)
        
        mock_clientes = [MagicMock() for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_clientes
        mock_session.execute.return_value = mock_result
        
        # Test con diferentes ordenamientos
        sort_fields = ["nombre", "nit", "codigo_unico", "created_at"]
        
        for sort_field in sort_fields:
            resultado = await repo.listar_clientes(
                limite=10,
                offset=0,
                ordenar_por=sort_field
            )
            assert len(resultado) == 3
        
        assert mock_session.execute.call_count == len(sort_fields)

    @pytest.mark.asyncio
    async def test_edge_cases_empty_results(self, mock_session):
        """Test: Casos edge con resultados vacíos"""
        repo = ClienteRepository(mock_session)
        
        # Mock resultado vacío
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result
        
        # Test listado vacío
        resultado = await repo.listar_clientes()
        assert len(resultado) == 0
        
        # Test conteo cero
        total = await repo.contar_clientes()
        assert total == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])