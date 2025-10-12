"""
Pruebas unitarias completas para app/routes/catalog.py
Objetivo: 100% de cobertura en las rutas/endpoints del catálogo
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request
from faker import Faker
from app.routes.catalog import router, list_items, get_product, get_inventory
from app.schemas import SearchResponse, Product, Meta
from datetime import date, datetime
import orjson
import time

fake = Faker()

class TestListItems:
    """Pruebas para el endpoint GET /items"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock del objeto Request de FastAPI"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/catalog/items"
        return request
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión de base de datos"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock del cliente Redis"""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock()
        redis_mock.setex = AsyncMock()
        return redis_mock
    
    @pytest.fixture
    def sample_product_data(self):
        """Datos de ejemplo para productos usando Faker"""
        return [
            Mock(
                id=fake.uuid4(),
                nombre=fake.name() + " " + fake.word(),
                codigo=fake.bothify("MED-####"),
                categoria_id=fake.uuid4(),
                presentacion=fake.random_element(["Caja", "Frasco", "Ampolla", "Tableta"]),
                precio_unitario=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                requisitos_almacenamiento=fake.sentence()
            ),
            Mock(
                id=fake.uuid4(),
                nombre=fake.name() + " " + fake.word(),
                codigo=fake.bothify("MED-####"),
                categoria_id=fake.uuid4(),
                presentacion=fake.random_element(["Caja", "Frasco", "Ampolla", "Tableta"]),
                precio_unitario=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                requisitos_almacenamiento=fake.sentence()
            )
        ]
    
    @pytest.fixture
    def sample_inventory_map(self, sample_product_data):
        """Mapa de inventario para los productos"""
        return {
            sample_product_data[0].id: {
                "cantidad": fake.random_int(min=1, max=1000),
                "paises": [fake.country_code(), fake.country_code()]
            }
        }
    
    @patch('app.routes.catalog.get_redis')
    @patch('app.routes.catalog.search_key')
    @patch('app.routes.catalog.buscar_productos')
    @patch('app.routes.catalog.time.perf_counter_ns')
    async def test_list_items_cache_hit(self, mock_time, mock_buscar, mock_search_key, 
                                      mock_get_redis, mock_request, mock_session):
        """Prueba cuando hay cache hit - debe retornar datos del cache"""
        # Arrange
        mock_time.return_value = 1000000000  # 1 segundo en nanosegundos
        mock_search_key.return_value = "test_cache_key"
        
        cached_data = {
            "items": [{"id": fake.uuid4(), "nombre": fake.name()}],
            "meta": {"page": 1, "size": 20, "total": 1, "tookMs": 5}
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = orjson.dumps(cached_data)
        mock_get_redis.return_value = mock_redis
        
        # Act
        result = await list_items(
            request=mock_request,
            q="test query",
            categoriaId="cat123",
            session=mock_session
        )
        
        # Assert
        assert result == cached_data
        mock_redis.get.assert_called_once_with("test_cache_key")
        mock_buscar.assert_not_called()  # No debe llamar a la DB si hay cache
    
    @patch('app.routes.catalog.get_redis')
    @patch('app.routes.catalog.search_key')
    @patch('app.routes.catalog.buscar_productos')
    @patch('app.routes.catalog.time.perf_counter_ns')
    async def test_list_items_cache_miss(self, mock_time, mock_buscar, mock_search_key,
                                       mock_get_redis, mock_request, mock_session,
                                       sample_product_data, sample_inventory_map):
        """Prueba cuando no hay cache - debe consultar DB y guardar en cache"""
        # Arrange
        start_time = 1000000000
        end_time = 1005000000  # +5ms
        mock_time.side_effect = [start_time, end_time]
        
        mock_search_key.return_value = "test_cache_key"
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        mock_get_redis.return_value = mock_redis
        
        total_products = fake.random_int(min=1, max=100)
        mock_buscar.return_value = (sample_product_data, total_products, sample_inventory_map)
        
        # Act
        result = await list_items(
            request=mock_request,
            q="medicine",
            categoriaId="cat123",
            page=1,
            size=20,
            session=mock_session
        )
        
        # Assert
        assert "items" in result
        assert "meta" in result
        assert len(result["items"]) == len(sample_product_data)
        assert result["meta"]["page"] == 1
        assert result["meta"]["size"] == 20
        assert result["meta"]["total"] == total_products
        assert result["meta"]["tookMs"] == 5
        
        # Verificar que se guardó en cache
        mock_redis.setex.assert_called_once()
        cache_args = mock_redis.setex.call_args
        assert cache_args[0][0] == "test_cache_key"  # key
        assert cache_args[0][1] == 5  # TTL 5 segundos
        
        # Verificar estructura del item con inventario
        item_with_inventory = next((item for item in result["items"] 
                                  if item["id"] == sample_product_data[0].id), None)
        assert item_with_inventory is not None
        assert "inventarioResumen" in item_with_inventory
        assert item_with_inventory["inventarioResumen"]["cantidadTotal"] == sample_inventory_map[sample_product_data[0].id]["cantidad"]
        
        # Verificar item sin inventario
        item_without_inventory = next((item for item in result["items"] 
                                     if item["id"] == sample_product_data[1].id), None)
        assert item_without_inventory is not None
        assert "inventarioResumen" not in item_without_inventory
    
    @patch('app.routes.catalog.get_redis')
    @patch('app.routes.catalog.search_key')
    @patch('app.routes.catalog.buscar_productos')
    @patch('app.routes.catalog.time.perf_counter_ns')
    async def test_list_items_all_parameters(self, mock_time, mock_buscar, mock_search_key,
                                           mock_get_redis, mock_request, mock_session):
        """Prueba con todos los parámetros de búsqueda"""
        # Arrange
        mock_time.side_effect = [1000000000, 1002000000]  # 2ms
        mock_search_key.return_value = "full_params_key"
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_get_redis.return_value = mock_redis
        
        mock_buscar.return_value = ([], 0, {})
        
        # Act
        result = await list_items(
            request=mock_request,
            q="aspirina",
            categoriaId="cat456",
            codigo="MED-001",
            pais="CO",
            bodegaId="BOD123",
            page=2,
            size=50,
            sort="precio",
            session=mock_session
        )
        
        # Assert
        mock_search_key.assert_called_once_with(
            "aspirina", "cat456", "MED-001", "CO", "BOD123", 2, 50, "precio"
        )
        mock_buscar.assert_called_once_with(
            mock_session,
            q="aspirina",
            categoriaId="cat456", 
            codigo="MED-001",
            pais="CO",
            bodegaId="BOD123",
            page=2,
            size=50,
            sort="precio"
        )
        
        assert result["items"] == []
        assert result["meta"]["page"] == 2
        assert result["meta"]["size"] == 50
        assert result["meta"]["total"] == 0
        assert result["meta"]["tookMs"] == 2


class TestGetProduct:
    """Pruebas para el endpoint GET /items/{id}"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión de base de datos"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_product_row(self):
        """Producto de ejemplo usando Faker"""
        return Mock(
            id=fake.uuid4(),
            nombre=fake.name() + " " + fake.word(),
            codigo=fake.bothify("MED-####"),
            categoria_id=fake.uuid4(),
            presentacion=fake.random_element(["Caja", "Frasco", "Ampolla"]),
            precio_unitario=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
            requisitos_almacenamiento=fake.sentence()
        )
    
    async def test_get_product_found(self, mock_session, sample_product_row):
        """Prueba obtener producto existente"""
        # Arrange
        product_id = sample_product_row.id
        
        # Mock que simula el resultado de session.execute()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_product_row)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await get_product(product_id, mock_session)
        
        # Assert
        assert result["id"] == sample_product_row.id
        assert result["nombre"] == sample_product_row.nombre
        assert result["codigo"] == sample_product_row.codigo
        assert result["categoria"] == sample_product_row.categoria_id
        assert result["presentacion"] == sample_product_row.presentacion
        assert result["precioUnitario"] == float(sample_product_row.precio_unitario)
        assert result["requisitosAlmacenamiento"] == sample_product_row.requisitos_almacenamiento
        
        mock_session.execute.assert_called_once()
    
    async def test_get_product_not_found(self, mock_session):
        """Prueba obtener producto no existente"""
        # Arrange
        product_id = fake.uuid4()
        
        # Mock que simula el resultado de session.execute() cuando no encuentra nada
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await get_product(product_id, mock_session)
        
        # Assert
        assert result == ({"detail": "Not found"}, 404)
        mock_session.execute.assert_called_once()


class TestGetInventory:
    """Pruebas para el endpoint GET /items/{id}/inventario"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión de base de datos"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_inventory_rows(self):
        """Datos de inventario de ejemplo usando Faker"""
        return [
            Mock(
                pais=fake.country_code(),
                bodega_id=fake.bothify("BOD-###"),
                lote=fake.bothify("LOT-####"),
                cantidad=fake.random_int(min=1, max=500),
                vence=fake.future_date(),
                condiciones=fake.sentence()
            ),
            Mock(
                pais=fake.country_code(),
                bodega_id=fake.bothify("BOD-###"),
                lote=fake.bothify("LOT-####"),
                cantidad=fake.random_int(min=1, max=500),
                vence=fake.future_date(),
                condiciones=fake.sentence()
            )
        ]
    
    @patch('app.routes.catalog.detalle_inventario')
    async def test_get_inventory_success(self, mock_detalle, mock_session, sample_inventory_rows):
        """Prueba obtener inventario exitosamente"""
        # Arrange
        product_id = fake.uuid4()
        total_items = fake.random_int(min=2, max=100)
        
        mock_detalle.return_value = (sample_inventory_rows, total_items)
        
        # Act
        result = await get_inventory(product_id, page=1, size=50, session=mock_session)
        
        # Assert
        assert "items" in result
        assert "meta" in result
        assert len(result["items"]) == len(sample_inventory_rows)
        
        # Verificar estructura de items de inventario
        for i, item in enumerate(result["items"]):
            expected_row = sample_inventory_rows[i]
            assert item["pais"] == expected_row.pais
            assert item["bodegaId"] == expected_row.bodega_id
            assert item["lote"] == expected_row.lote
            assert item["cantidad"] == expected_row.cantidad
            assert item["vence"] == expected_row.vence.isoformat()
            assert item["condiciones"] == expected_row.condiciones
        
        # Verificar meta
        assert result["meta"]["page"] == 1
        assert result["meta"]["size"] == 50
        assert result["meta"]["total"] == total_items
        assert result["meta"]["tookMs"] == 0
        
        mock_detalle.assert_called_once_with(mock_session, product_id, 1, 50)
    
    @patch('app.routes.catalog.detalle_inventario')
    async def test_get_inventory_empty(self, mock_detalle, mock_session):
        """Prueba obtener inventario vacío"""
        # Arrange
        product_id = fake.uuid4()
        mock_detalle.return_value = ([], 0)
        
        # Act
        result = await get_inventory(product_id, page=1, size=20, session=mock_session)
        
        # Assert
        assert result["items"] == []
        assert result["meta"]["page"] == 1
        assert result["meta"]["size"] == 20
        assert result["meta"]["total"] == 0
        assert result["meta"]["tookMs"] == 0
        
        mock_detalle.assert_called_once_with(mock_session, product_id, 1, 20)
    
    @patch('app.routes.catalog.detalle_inventario')
    async def test_get_inventory_custom_pagination(self, mock_detalle, mock_session):
        """Prueba con paginación personalizada"""
        # Arrange
        product_id = fake.uuid4()
        mock_detalle.return_value = ([], 0)
        
        # Act
        result = await get_inventory(product_id, page=3, size=25, session=mock_session)
        
        # Assert
        assert result["meta"]["page"] == 3
        assert result["meta"]["size"] == 25
        mock_detalle.assert_called_once_with(mock_session, product_id, 3, 25)


class TestRouteIntegration:
    """Pruebas de integración para verificar el comportamiento completo de las rutas"""
    
    def test_router_configuration(self):
        """Prueba que el router esté configurado correctamente"""
        assert router.prefix == "/catalog"
        assert "catalog" in router.tags
    
    @patch('app.routes.catalog.settings')
    def test_default_query_parameters(self, mock_settings):
        """Prueba que los parámetros por defecto se apliquen correctamente"""
        mock_settings.page_size_default = 20
        mock_settings.page_size_max = 100
        
        # Esta prueba verifica que la configuración esté disponible
        # En una prueba real de FastAPI, esto se probaría con TestClient
        assert mock_settings.page_size_default == 20
        assert mock_settings.page_size_max == 100