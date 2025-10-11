import pytest
from unittest.mock import AsyncMock, patch
from faker import Faker
from fastapi.testclient import TestClient
import json
from app.main import app
from tests.factories import generate_test_productos, generate_test_inventario

fake = Faker(['es_ES'])

class TestCatalogRoutes:
    """Pruebas para los endpoints del catálogo."""

    @pytest.mark.unit
    def test_list_items_sin_parametros(self, test_client):
        """Prueba endpoint de listar items sin parámetros."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(5)
            mock_buscar.return_value = (productos_mock, 5, {})
            
            # Act
            response = test_client.get("/api/catalog/items")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "meta" in data
            assert data["meta"]["total"] == 5
            assert data["meta"]["page"] == 1
            assert data["meta"]["size"] == 20  # default
            assert "tookMs" in data["meta"]

    @pytest.mark.unit
    def test_list_items_con_busqueda(self, test_client):
        """Prueba búsqueda por nombre."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = [p for p in generate_test_productos(1) if 'amoxicilina' in p.nombre.lower()]
            if not productos_mock:  # Forzar un producto con amoxicilina
                productos_mock = generate_test_productos(1)
                productos_mock[0].nombre = "Amoxicilina 500mg"
            
            mock_buscar.return_value = (productos_mock, 1, {})
            
            # Act
            response = test_client.get("/api/catalog/items?q=amoxicilina")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["total"] == 1
            mock_buscar.assert_called_once()

    @pytest.mark.unit
    def test_list_items_con_paginacion(self, test_client):
        """Prueba paginación."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(10)
            mock_buscar.return_value = (productos_mock, 25, {})
            
            # Act
            response = test_client.get("/api/catalog/items?page=2&size=10")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["page"] == 2
            assert data["meta"]["size"] == 10
            assert data["meta"]["total"] == 25

    @pytest.mark.unit
    def test_list_items_filtro_categoria(self, test_client):
        """Prueba filtro por categoría."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(3)
            for p in productos_mock:
                p.categoria_id = "ANTIBIOTICS"
            mock_buscar.return_value = (productos_mock, 3, {})
            
            # Act
            response = test_client.get("/api/catalog/items?categoriaId=ANTIBIOTICS")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["total"] == 3
            for item in data["items"]:
                assert item["categoria"] == "ANTIBIOTICS"

    @pytest.mark.unit
    def test_list_items_filtro_codigo(self, test_client):
        """Prueba filtro por código."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange  
            producto_mock = generate_test_productos(1)
            producto_mock[0].codigo = "AMX500"
            mock_buscar.return_value = (producto_mock, 1, {})
            
            # Act
            response = test_client.get("/api/catalog/items?codigo=AMX500")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["total"] == 1
            assert data["items"][0]["codigo"] == "AMX500"

    @pytest.mark.unit
    def test_list_items_con_inventario_resumen(self, test_client):
        """Prueba respuesta con resumen de inventario."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(2)
            inv_map = {
                productos_mock[0].id: {"cantidad": 1500, "paises": ["CO", "MX"]},
                productos_mock[1].id: {"cantidad": 800, "paises": ["PE"]}
            }
            mock_buscar.return_value = (productos_mock, 2, inv_map)
            
            # Act
            response = test_client.get("/api/catalog/items")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar que algunos items tengan inventario
            items_con_inventario = [item for item in data["items"] if "inventarioResumen" in item]
            assert len(items_con_inventario) >= 1

    @pytest.mark.unit
    def test_list_items_ordenamiento(self, test_client):
        """Prueba ordenamiento por precio."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(3)
            # Ordenar por precio para simular resultado
            productos_mock.sort(key=lambda x: x.precio_unitario)
            mock_buscar.return_value = (productos_mock, 3, {})
            
            # Act
            response = test_client.get("/api/catalog/items?sort=precio")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 3

    @pytest.mark.unit
    def test_list_items_parametros_invalidos(self, test_client):
        """Prueba validación de parámetros."""
        # Page inválido
        response = test_client.get("/api/catalog/items?page=0")
        assert response.status_code == 422  # Validation error
        
        # Size mayor al máximo
        response = test_client.get("/api/catalog/items?size=1000")
        assert response.status_code == 422

        # Sort inválido
        response = test_client.get("/api/catalog/items?sort=invalid")
        assert response.status_code == 422

    @pytest.mark.unit
    def test_get_product_exitoso(self, test_client):
        """Prueba obtener producto específico."""
        with patch('app.routes.catalog.session') as mock_session, \
             patch('app.routes.catalog.select') as mock_select:
            
            # Arrange
            producto_mock = generate_test_productos(1)[0]
            producto_mock.id = "TEST001"
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = producto_mock
            mock_session.execute.return_value = mock_result
            
            # Act
            response = test_client.get("/api/catalog/items/TEST001")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "TEST001"

    @pytest.mark.unit
    def test_get_product_no_encontrado(self, test_client):
        """Prueba producto no encontrado."""
        with patch('app.routes.catalog.session') as mock_session:
            # Arrange
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            # Act
            response = test_client.get("/api/catalog/items/INEXISTENTE")
            
            # Assert
            assert response.status_code == 404

    @pytest.mark.unit
    def test_get_inventory_exitoso(self, test_client):
        """Prueba obtener inventario de producto."""
        with patch('app.repositories.catalog_repo.detalle_inventario') as mock_detalle:
            # Arrange
            inventarios_mock = generate_test_inventario(["TEST001"], 3)
            mock_detalle.return_value = (inventarios_mock, 3)
            
            # Act
            response = test_client.get("/api/catalog/items/TEST001/inventario")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "meta" in data
            assert data["meta"]["total"] == 3
            assert len(data["items"]) == 3

    @pytest.mark.unit
    def test_get_inventory_con_paginacion(self, test_client):
        """Prueba paginación en inventario."""
        with patch('app.repositories.catalog_repo.detalle_inventario') as mock_detalle:
            # Arrange
            inventarios_mock = generate_test_inventario(["TEST001"], 5)
            mock_detalle.return_value = (inventarios_mock, 15)  # Total 15
            
            # Act
            response = test_client.get("/api/catalog/items/TEST001/inventario?page=2&size=5")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["page"] == 2
            assert data["meta"]["size"] == 5
            assert data["meta"]["total"] == 15

    @pytest.mark.unit
    def test_performance_metrics(self, test_client):
        """Prueba que se incluyan métricas de rendimiento."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar:
            # Arrange
            productos_mock = generate_test_productos(1)
            mock_buscar.return_value = (productos_mock, 1, {})
            
            # Act
            response = test_client.get("/api/catalog/items")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "tookMs" in data["meta"]
            assert isinstance(data["meta"]["tookMs"], int)
            assert data["meta"]["tookMs"] >= 0

class TestCacheIntegration:
    """Pruebas de integración con caché."""

    @pytest.mark.unit
    def test_cache_miss_then_hit(self, test_client, fake_redis):
        """Prueba cache miss seguido de cache hit."""
        with patch('app.repositories.catalog_repo.buscar_productos') as mock_buscar, \
             patch('app.routes.catalog.get_redis') as mock_get_redis:
            
            # Arrange
            mock_get_redis.return_value = fake_redis
            productos_mock = generate_test_productos(2)
            mock_buscar.return_value = (productos_mock, 2, {})
            
            # Act - Primera llamada (cache miss)
            response1 = test_client.get("/api/catalog/items?q=test")
            assert response1.status_code == 200
            
            # Segunda llamada debería usar caché
            response2 = test_client.get("/api/catalog/items?q=test")
            assert response2.status_code == 200
            
            # Assert - Verificar que buscar_productos solo se llamó una vez
            assert mock_buscar.call_count == 1