"""
Pruebas unitarias completas para app/repositories/catalog_repo.py
Objetivo: 100% de cobertura sin usar base de datos real
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from faker import Faker
from app.repositories.catalog_repo import buscar_productos, detalle_inventario
from datetime import date, datetime

fake = Faker()

class TestBuscarProductos:
    """Pruebas para la función buscar_productos"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión AsyncSession"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_productos(self):
        """Productos de ejemplo usando Faker"""
        return [
            Mock(
                id=fake.uuid4(),
                nombre=fake.name() + " " + fake.word(),
                codigo=fake.bothify("MED-####"),
                categoria_id=fake.uuid4(),
                presentacion=fake.random_element(["Caja", "Frasco", "Ampolla"]),
                precio_unitario=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                requisitos_almacenamiento=fake.sentence(),
                activo=True
            ),
            Mock(
                id=fake.uuid4(),
                nombre=fake.name() + " " + fake.word(),
                codigo=fake.bothify("MED-####"),
                categoria_id=fake.uuid4(),
                presentacion=fake.random_element(["Caja", "Frasco", "Ampolla"]),
                precio_unitario=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                requisitos_almacenamiento=fake.sentence(),
                activo=True
            )
        ]
    
    @pytest.fixture 
    def sample_inventario(self, sample_productos):
        """Inventario de ejemplo usando Faker"""
        return [
            Mock(
                producto_id=sample_productos[0].id,
                cantidad=fake.random_int(min=10, max=100),
                paises=[fake.country_code(), fake.country_code()]
            ),
            Mock(
                producto_id=sample_productos[1].id,
                cantidad=fake.random_int(min=5, max=50),
                paises=[fake.country_code()]
            )
        ]
    
    async def test_buscar_productos_sin_filtros(self, mock_session, sample_productos, sample_inventario):
        """Prueba búsqueda básica sin filtros"""
        # Arrange
        total_count = len(sample_productos)
        
        # Mock para el conteo
        count_result = Mock()
        count_result.scalar_one.return_value = total_count
        
        # Mock para los productos
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = sample_productos
        
        # Mock para el inventario
        inventory_result = Mock()
        inventory_result.all.return_value = sample_inventario
        
        # Configurar session.execute para retornar diferentes resultados según la llamada
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert rows == sample_productos
        assert total == total_count
        assert len(inv_map) == len(sample_inventario)
        assert mock_session.execute.call_count == 3  # count + products + inventory
        
        # Verificar estructura del inventory map
        for inv in sample_inventario:
            assert inv.producto_id in inv_map
            assert inv_map[inv.producto_id]["cantidad"] == int(inv.cantidad)
            assert inv_map[inv.producto_id]["paises"] == list(inv.paises)
    
    async def test_buscar_productos_con_query_texto(self, mock_session, sample_productos):
        """Prueba búsqueda con filtro de texto"""
        # Arrange
        query_text = "medicina"
        
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        
        products_result = Mock() 
        products_result.scalars.return_value.all.return_value = [sample_productos[0]]
        
        inventory_result = Mock()
        inventory_result.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=query_text,
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert len(rows) == 1
        assert total == 1
        assert inv_map == {}
    
    async def test_buscar_productos_con_categoria(self, mock_session, sample_productos):
        """Prueba búsqueda con filtro de categoría"""
        # Arrange
        categoria_id = fake.uuid4()
        
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = [sample_productos[0]]
        
        inventory_result = Mock()
        inventory_result.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=categoria_id,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert len(rows) == 1
        assert total == 1
        assert inv_map == {}
    
    async def test_buscar_productos_con_codigo(self, mock_session, sample_productos):
        """Prueba búsqueda con filtro de código"""
        # Arrange
        codigo = "MED-001"
        
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = [sample_productos[0]]
        
        inventory_result = Mock()
        inventory_result.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=codigo,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert len(rows) == 1
        assert total == 1
        assert inv_map == {}
    
    async def test_buscar_productos_orden_por_precio(self, mock_session, sample_productos, sample_inventario):
        """Prueba ordenamiento por precio"""
        # Arrange
        count_result = Mock()
        count_result.scalar_one.return_value = len(sample_productos)
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = sample_productos
        
        inventory_result = Mock()
        inventory_result.all.return_value = sample_inventario
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort="precio"
        )
        
        # Assert
        assert rows == sample_productos
        assert total == len(sample_productos)
        assert len(inv_map) == len(sample_inventario)
    
    async def test_buscar_productos_orden_por_defecto(self, mock_session, sample_productos, sample_inventario):
        """Prueba ordenamiento por defecto (nombre)"""
        # Arrange
        count_result = Mock()
        count_result.scalar_one.return_value = len(sample_productos)
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = sample_productos
        
        inventory_result = Mock()
        inventory_result.all.return_value = sample_inventario
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort="nombre"  # Cualquier valor que no sea "precio"
        )
        
        # Assert
        assert rows == sample_productos
        assert total == len(sample_productos)
        assert len(inv_map) == len(sample_inventario)
    
    async def test_buscar_productos_sin_resultados(self, mock_session):
        """Prueba cuando no hay productos que coincidan"""
        # Arrange
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, products_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q="producto_inexistente",
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert rows == []
        assert total == 0
        assert inv_map == []  # Retorna lista vacía cuando no hay IDs
    
    async def test_buscar_productos_con_filtros_inventario(self, mock_session, sample_productos, sample_inventario):
        """Prueba búsqueda con filtros de país y bodega en inventario"""
        # Arrange
        pais_filtro = "CO"
        bodega_filtro = "BOD001"
        
        count_result = Mock()
        count_result.scalar_one.return_value = len(sample_productos)
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = sample_productos
        
        inventory_result = Mock()
        inventory_result.all.return_value = sample_inventario
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=None,
            pais=pais_filtro,
            bodegaId=bodega_filtro,
            page=1,
            size=20,
            sort=None
        )
        
        # Assert
        assert rows == sample_productos
        assert total == len(sample_productos)
        assert len(inv_map) == len(sample_inventario)
    
    async def test_buscar_productos_paginacion(self, mock_session, sample_productos, sample_inventario):
        """Prueba paginación"""
        # Arrange
        page = 2
        size = 10
        
        count_result = Mock()
        count_result.scalar_one.return_value = 25  # Total de productos
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = sample_productos
        
        inventory_result = Mock()
        inventory_result.all.return_value = sample_inventario
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q=None,
            categoriaId=None,
            codigo=None,
            pais=None,
            bodegaId=None,
            page=page,
            size=size,
            sort=None
        )
        
        # Assert
        assert rows == sample_productos
        assert total == 25
        assert len(inv_map) == len(sample_inventario)
    
    async def test_buscar_productos_todos_los_filtros(self, mock_session, sample_productos):
        """Prueba con todos los filtros combinados"""
        # Arrange
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        
        products_result = Mock()
        products_result.scalars.return_value.all.return_value = [sample_productos[0]]
        
        inventory_result = Mock()
        inventory_result.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, products_result, inventory_result]
        
        # Act
        rows, total, inv_map = await buscar_productos(
            session=mock_session,
            q="medicina",
            categoriaId="cat123",
            codigo="MED-001",
            pais="CO",
            bodegaId="BOD001",
            page=1,
            size=5,
            sort="precio"
        )
        
        # Assert
        assert len(rows) == 1
        assert total == 1
        assert inv_map == {}


class TestDetalleInventario:
    """Pruebas para la función detalle_inventario"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión AsyncSession"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_inventario_detalle(self):
        """Inventario detallado de ejemplo usando Faker"""
        return [
            Mock(
                id=fake.random_int(min=1, max=1000),
                producto_id=fake.uuid4(),
                pais=fake.country_code(),
                bodega_id=fake.bothify("BOD-###"),
                lote=fake.bothify("LOT-####"),
                cantidad=fake.random_int(min=1, max=500),
                vence=fake.future_date(),
                condiciones=fake.sentence()
            ),
            Mock(
                id=fake.random_int(min=1, max=1000),
                producto_id=fake.uuid4(),
                pais=fake.country_code(),
                bodega_id=fake.bothify("BOD-###"),
                lote=fake.bothify("LOT-####"),
                cantidad=fake.random_int(min=1, max=500),
                vence=fake.future_date(),
                condiciones=fake.sentence()
            )
        ]
    
    async def test_detalle_inventario_existente(self, mock_session, sample_inventario_detalle):
        """Prueba obtener detalle de inventario existente"""
        # Arrange
        producto_id = fake.uuid4()
        page = 1
        size = 20
        total_items = len(sample_inventario_detalle)
        
        # Mock para el conteo
        count_result = Mock()
        count_result.scalar_one.return_value = total_items
        
        # Mock para los detalles
        details_result = Mock()
        details_result.scalars.return_value.all.return_value = sample_inventario_detalle
        
        mock_session.execute.side_effect = [count_result, details_result]
        
        # Act
        rows, total = await detalle_inventario(mock_session, producto_id, page, size)
        
        # Assert
        assert rows == sample_inventario_detalle
        assert total == total_items
        assert mock_session.execute.call_count == 2  # count + details
    
    async def test_detalle_inventario_vacio(self, mock_session):
        """Prueba obtener detalle de inventario vacío"""
        # Arrange
        producto_id = fake.uuid4()
        page = 1
        size = 20
        
        # Mock para el conteo
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        
        # Mock para los detalles
        details_result = Mock()
        details_result.scalars.return_value.all.return_value = []
        
        mock_session.execute.side_effect = [count_result, details_result]
        
        # Act
        rows, total = await detalle_inventario(mock_session, producto_id, page, size)
        
        # Assert
        assert rows == []
        assert total == 0
        assert mock_session.execute.call_count == 2
    
    async def test_detalle_inventario_paginacion_personalizada(self, mock_session, sample_inventario_detalle):
        """Prueba con paginación personalizada"""
        # Arrange
        producto_id = fake.uuid4()
        page = 3
        size = 5
        total_items = 50
        
        # Mock para el conteo
        count_result = Mock()
        count_result.scalar_one.return_value = total_items
        
        # Mock para los detalles
        details_result = Mock()
        details_result.scalars.return_value.all.return_value = sample_inventario_detalle
        
        mock_session.execute.side_effect = [count_result, details_result]
        
        # Act
        rows, total = await detalle_inventario(mock_session, producto_id, page, size)
        
        # Assert
        assert rows == sample_inventario_detalle
        assert total == total_items
        assert mock_session.execute.call_count == 2
    
    async def test_detalle_inventario_productos_diferentes(self, mock_session, sample_inventario_detalle):
        """Prueba con diferentes IDs de producto"""
        # Arrange
        producto_ids = [fake.uuid4() for _ in range(3)]
        
        for producto_id in producto_ids:
            count_result = Mock()
            count_result.scalar_one.return_value = len(sample_inventario_detalle)
            
            details_result = Mock()
            details_result.scalars.return_value.all.return_value = sample_inventario_detalle
            
            mock_session.execute.side_effect = [count_result, details_result]
            
            # Act
            rows, total = await detalle_inventario(mock_session, producto_id, 1, 50)
            
            # Assert
            assert rows == sample_inventario_detalle
            assert total == len(sample_inventario_detalle)
            
            # Reset para la siguiente iteración
            mock_session.execute.side_effect = None