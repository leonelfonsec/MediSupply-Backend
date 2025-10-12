import pytest
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
from app.repositories.catalog_repo import buscar_productos, detalle_inventario
from app.models.catalogo_model import Producto, Inventario
from tests.factories import ProductoFactory, InventarioFactory, generate_test_productos, generate_test_inventario

fake = Faker(['es_ES'])

def setup_mock_session_execute(mock_session, count_value, data_list, inventory_list=None):
    """
    Función auxiliar para configurar correctamente el mock de session.execute 
    para manejar múltiples llamadas SQLAlchemy async.
    """
    if inventory_list is None:
        inventory_list = []
    
    # Mock para el count query
    count_result = MagicMock()
    count_result.scalar_one.return_value = count_value
    
    # Mock para el data query
    data_result = MagicMock()
    data_scalars = MagicMock()
    data_scalars.all.return_value = data_list
    data_result.scalars.return_value = data_scalars
    
    # Mock para el inventory query
    inv_result = MagicMock()
    inv_result.all.return_value = inventory_list
    
    # Configurar side_effect para múltiples llamadas en orden
    mock_session.execute.side_effect = [count_result, data_result, inv_result]
    
    return mock_session

def setup_mock_session_simple(mock_session, count_value, data_list):
    """
    Función auxiliar para configurar mock de session.execute para funciones
    que solo hacen count + data queries (como detalle_inventario).
    """
    # Mock para el count query
    count_result = MagicMock()
    count_result.scalar_one.return_value = count_value
    
    # Mock para el data query
    data_result = MagicMock()
    data_scalars = MagicMock()
    data_scalars.all.return_value = data_list
    data_result.scalars.return_value = data_scalars
    
    # Configurar side_effect para 2 llamadas
    mock_session.execute.side_effect = [count_result, data_result]
    
    return mock_session

class TestBuscarProductos:
    """Pruebas para la función buscar_productos."""

    @pytest.mark.unit
    async def test_buscar_productos_sin_filtros(self, mock_session):
        """Prueba búsqueda sin filtros aplicados."""
        # Arrange
        productos_mock = generate_test_productos(5)
        setup_mock_session_execute(mock_session, 5, productos_mock)
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session, 
            q=None, categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert len(productos) == 5
        assert total == 5
        assert isinstance(inv_map, dict)
        assert mock_session.execute.call_count >= 2  # Una para count, otra para datos

    @pytest.mark.unit 
    async def test_buscar_productos_por_nombre(self, mock_session):
        """Prueba búsqueda por nombre."""
        # Arrange
        productos_mock = [ProductoFactory(nombre="Amoxicilina 500mg")]
        setup_mock_session_execute(mock_session, 1, productos_mock)
        mock_session.execute.return_value.all.return_value = []  # Sin inventario
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q="amoxicilina", categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert total == 1
        assert len(productos) == 1
        assert "amoxicilina" in productos[0].nombre.lower()

    @pytest.mark.unit
    async def test_buscar_productos_por_categoria(self, mock_session):
        """Prueba búsqueda por categoría."""
        # Arrange
        productos_mock = [
            ProductoFactory(categoria_id="ANTIBIOTICS"),
            ProductoFactory(categoria_id="ANTIBIOTICS")
        ]
        setup_mock_session_execute(mock_session, 2, productos_mock)
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q=None, categoriaId="ANTIBIOTICS", codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert total == 2
        assert all(p.categoria_id == "ANTIBIOTICS" for p in productos)

    @pytest.mark.unit
    async def test_buscar_productos_por_codigo(self, mock_session):
        """Prueba búsqueda por código específico."""
        # Arrange
        producto_mock = ProductoFactory(codigo="AMX500")
        setup_mock_session_execute(mock_session, 1, [producto_mock])
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q=None, categoriaId=None, codigo="AMX500",
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert total == 1
        assert productos[0].codigo == "AMX500"

    @pytest.mark.unit
    async def test_buscar_productos_paginacion(self, mock_session):
        """Prueba paginación correcta."""
        # Arrange - Página 2 con size 5
        productos_mock = generate_test_productos(5)
        setup_mock_session_execute(mock_session, 25, productos_mock)
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q=None, categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=2, size=5, sort=None
        )
        
        # Assert
        assert total == 25
        assert len(productos) == 5
        # Verificar que se aplicó el offset correcto (page=2, size=5 -> offset=5)

    @pytest.mark.unit
    async def test_buscar_productos_ordenamiento_precio(self, mock_session):
        """Prueba ordenamiento por precio."""
        # Arrange
        productos_mock = generate_test_productos(3)
        setup_mock_session_execute(mock_session, 3, productos_mock)
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q=None, categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort="precio"
        )
        
        # Assert
        assert total == 3
        assert len(productos) == 3

    @pytest.mark.unit
    async def test_buscar_productos_con_inventario(self, mock_session):
        """Prueba búsqueda con datos de inventario."""
        # Arrange
        productos_mock = [ProductoFactory(id="PROD001")]
        inventario_mock_row = MagicMock()
        inventario_mock_row.producto_id = "PROD001"
        inventario_mock_row.cantidad = 1500
        inventario_mock_row.paises = ["CO", "MX"]
        
        setup_mock_session_execute(mock_session, 1, productos_mock, [inventario_mock_row])
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q=None, categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert total == 1
        assert "PROD001" in inv_map
        assert inv_map["PROD001"]["cantidad"] == 1500
        assert inv_map["PROD001"]["paises"] == ["CO", "MX"]

    @pytest.mark.unit
    async def test_buscar_productos_sin_resultados(self, mock_session):
        """Prueba cuando no hay productos que coincidan."""
        # Arrange
        setup_mock_session_execute(mock_session, 0, [])
        
        # Act
        productos, total, inv_map = await buscar_productos(
            mock_session,
            q="producto_inexistente", categoriaId=None, codigo=None,
            pais=None, bodegaId=None, page=1, size=10, sort=None
        )
        
        # Assert
        assert total == 0
        assert len(productos) == 0
        assert inv_map == []

class TestDetalleInventario:
    """Pruebas para la función detalle_inventario."""

    @pytest.mark.unit
    async def test_detalle_inventario_exitoso(self, mock_session):
        """Prueba detalle de inventario exitoso."""
        # Arrange
        inventarios_mock = generate_test_inventario(["PROD001"], 3)
        setup_mock_session_simple(mock_session, 3, inventarios_mock)
        
        # Act
        inventarios, total = await detalle_inventario(mock_session, "PROD001", 1, 10)
        
        # Assert
        assert total == 3
        assert len(inventarios) == 3
        assert all(inv.producto_id == "PROD001" for inv in inventarios)

    @pytest.mark.unit
    async def test_detalle_inventario_paginacion(self, mock_session):
        """Prueba paginación en detalle de inventario."""
        # Arrange
        inventarios_mock = generate_test_inventario(["PROD001"], 5)
        setup_mock_session_simple(mock_session, 15, inventarios_mock)
        
        # Act - Página 2, tamaño 5
        inventarios, total = await detalle_inventario(mock_session, "PROD001", 2, 5)
        
        # Assert
        assert total == 15
        assert len(inventarios) == 5

    @pytest.mark.unit
    async def test_detalle_inventario_producto_sin_stock(self, mock_session):
        """Prueba producto sin inventario."""
        # Arrange
        setup_mock_session_simple(mock_session, 0, [])
        
        # Act
        inventarios, total = await detalle_inventario(mock_session, "PROD_SIN_STOCK", 1, 10)
        
        # Assert
        assert total == 0
        assert len(inventarios) == 0