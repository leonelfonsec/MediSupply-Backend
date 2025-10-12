"""
Pruebas unitarias completas para app/cache.py
Objetivo: 100% de cobertura de las funciones de cache
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
from faker import Faker
from app.cache import get_redis, search_key, set_cache, get_cache, delete_cache_pattern, invalidate_product_cache

fake = Faker()

class TestCacheOperations:
    """Pruebas para las operaciones de cache"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock del cliente Redis"""
        return AsyncMock()
    
    @patch('app.cache.redis.from_url')
    async def test_get_redis_primera_conexion(self, mock_from_url):
        """Prueba obtener Redis por primera vez"""
        # Arrange
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        # Limpiar cache global
        import app.cache
        app.cache._redis = None
        
        # Act
        result = await get_redis()
        
        # Assert
        assert result == mock_client
        mock_from_url.assert_called_once()
    
    @patch('app.cache.redis.from_url')
    async def test_get_redis_reutiliza_conexion(self, mock_from_url):
        """Prueba que reutiliza la conexión existente"""
        # Arrange
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        import app.cache
        app.cache._redis = mock_client
        
        # Act
        result = await get_redis()
        
        # Assert
        assert result == mock_client
        mock_from_url.assert_not_called()  # No debe crear nueva conexión
    
    def test_search_key_parametros_basicos(self):
        """Prueba generación de clave con parámetros básicos"""
        # Act
        key = search_key(q="medicina", page=2, size=10)
        
        # Assert
        expected = "catalog:search:q=medicina|cat=|cod=|pais=|bod=|p=2|s=10|sort="
        assert key == expected
    
    def test_search_key_todos_parametros(self):
        """Prueba generación de clave con todos los parámetros"""
        # Act
        key = search_key(
            q="aspirina",
            categoriaId="cat123",
            codigo="MED-001",
            pais="CO",
            bodegaId="BOD456", 
            page=3,
            size=25,
            sort="precio"
        )
        
        # Assert
        expected = "catalog:search:q=aspirina|cat=cat123|cod=MED-001|pais=CO|bod=BOD456|p=3|s=25|sort=precio"
        assert key == expected
    
    def test_search_key_parametros_nulos(self):
        """Prueba generación de clave con parámetros nulos"""
        # Act
        key = search_key(q=None, categoriaId=None, codigo=None, pais=None, bodegaId=None, sort=None)
        
        # Assert
        expected = "catalog:search:q=|cat=|cod=|pais=|bod=|p=1|s=20|sort="
        assert key == expected
    
    @patch('app.cache.get_redis')
    async def test_set_cache_exitoso(self, mock_get_redis, mock_redis_client):
        """Prueba guardar datos en cache exitosamente"""
        # Arrange
        mock_get_redis.return_value = mock_redis_client
        test_key = "test:key:123"
        test_data = {"productos": [{"id": fake.uuid4(), "nombre": fake.name()}]}
        test_ttl = 300
        
        # Act
        await set_cache(test_key, test_data, test_ttl)
        
        # Assert
        mock_redis_client.setex.assert_called_once_with(
            test_key, test_ttl, json.dumps(test_data)
        )
    
    @patch('app.cache.get_redis')
    async def test_set_cache_ttl_por_defecto(self, mock_get_redis, mock_redis_client):
        """Prueba guardar datos con TTL por defecto"""
        # Arrange
        mock_get_redis.return_value = mock_redis_client
        test_key = "test:key:default"
        test_data = {"message": fake.sentence()}
        
        # Act
        await set_cache(test_key, test_data)  # Sin TTL especificado
        
        # Assert
        mock_redis_client.setex.assert_called_once_with(
            test_key, 300, json.dumps(test_data)  # TTL por defecto: 300s
        )
    
    @patch('app.cache.get_redis')
    async def test_set_cache_error_redis(self, mock_get_redis, mock_redis_client):
        """Prueba manejo de error en Redis al guardar"""
        # Arrange
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.setex.side_effect = Exception("Redis connection error")
        
        test_key = "test:key:error"
        test_data = {"error": "test"}
        
        # Act - No debe lanzar excepción
        await set_cache(test_key, test_data)
        
        # Assert
        mock_redis_client.setex.assert_called_once()
    
    @patch('app.cache.get_redis')
    async def test_get_cache_hit(self, mock_get_redis, mock_redis_client):
        """Prueba obtener datos del cache (cache hit)"""
        # Arrange
        test_key = "test:key:hit"
        test_data = {"productos": [{"id": fake.uuid4()}]}
        json_data = json.dumps(test_data)
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.get.return_value = json_data
        
        # Act
        result = await get_cache(test_key)
        
        # Assert
        assert result == test_data
        mock_redis_client.get.assert_called_once_with(test_key)
    
    @patch('app.cache.get_redis')
    async def test_get_cache_miss(self, mock_get_redis, mock_redis_client):
        """Prueba obtener datos del cache (cache miss)"""
        # Arrange
        test_key = "test:key:miss"
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.get.return_value = None
        
        # Act
        result = await get_cache(test_key)
        
        # Assert
        assert result is None
        mock_redis_client.get.assert_called_once_with(test_key)
    
    @patch('app.cache.get_redis')
    async def test_get_cache_error_redis(self, mock_get_redis, mock_redis_client):
        """Prueba manejo de error en Redis al obtener"""
        # Arrange
        test_key = "test:key:error"
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.get.side_effect = Exception("Redis error")
        
        # Act
        result = await get_cache(test_key)
        
        # Assert
        assert result is None  # Debe retornar None en caso de error
        mock_redis_client.get.assert_called_once_with(test_key)
    
    @patch('app.cache.get_redis')
    async def test_delete_cache_pattern_con_claves(self, mock_get_redis, mock_redis_client):
        """Prueba eliminar claves que coinciden con patrón"""
        # Arrange
        pattern = "catalog:search:*"
        keys_encontradas = ["catalog:search:q=med", "catalog:search:q=asp"]
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.keys.return_value = keys_encontradas
        mock_redis_client.delete.return_value = len(keys_encontradas)
        
        # Act
        deleted_count = await delete_cache_pattern(pattern)
        
        # Assert
        assert deleted_count == len(keys_encontradas)
        mock_redis_client.keys.assert_called_once_with(pattern)
        mock_redis_client.delete.assert_called_once_with(*keys_encontradas)
    
    @patch('app.cache.get_redis')
    async def test_delete_cache_pattern_sin_claves(self, mock_get_redis, mock_redis_client):
        """Prueba eliminar patrón sin claves que coincidan"""
        # Arrange
        pattern = "catalog:search:*"
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.keys.return_value = []
        
        # Act
        deleted_count = await delete_cache_pattern(pattern)
        
        # Assert
        assert deleted_count == 0
        mock_redis_client.keys.assert_called_once_with(pattern)
        mock_redis_client.delete.assert_not_called()
    
    @patch('app.cache.get_redis')
    async def test_delete_cache_pattern_error(self, mock_get_redis, mock_redis_client):
        """Prueba manejo de error al eliminar patrón"""
        # Arrange
        pattern = "catalog:search:*"
        
        mock_get_redis.return_value = mock_redis_client
        mock_redis_client.keys.side_effect = Exception("Redis error")
        
        # Act
        deleted_count = await delete_cache_pattern(pattern)
        
        # Assert
        assert deleted_count == 0
        mock_redis_client.keys.assert_called_once_with(pattern)
    
    @patch('app.cache.delete_cache_pattern')
    async def test_invalidate_product_cache_sin_producto_id(self, mock_delete_pattern):
        """Prueba invalidar cache sin ID de producto específico"""
        # Arrange
        mock_delete_pattern.side_effect = [5, 3]  # Solo 2 patrones sin product_id
        
        # Act
        total_deleted = await invalidate_product_cache()
        
        # Assert
        assert total_deleted == 8  # 5 + 3
        assert mock_delete_pattern.call_count == 2
        
        # Verificar que se llamaron los patrones correctos
        expected_patterns = [
            "catalog:search:*",
            "catalog:category:*"
        ]
        actual_calls = [call[0][0] for call in mock_delete_pattern.call_args_list]
        assert all(pattern in actual_calls for pattern in expected_patterns)
    
    @patch('app.cache.delete_cache_pattern')
    async def test_invalidate_product_cache_con_producto_id(self, mock_delete_pattern):
        """Prueba invalidar cache con ID de producto específico"""
        # Arrange
        product_id = fake.uuid4()
        mock_delete_pattern.side_effect = [2, 1, 4]  # Retorna diferentes conteos
        
        # Act
        total_deleted = await invalidate_product_cache(product_id)
        
        # Assert
        assert total_deleted == 7  # 2 + 1 + 4
        assert mock_delete_pattern.call_count == 3
        
        # Verificar que se incluye el patrón del producto específico
        calls = [call[0][0] for call in mock_delete_pattern.call_args_list]
        assert f"catalog:product:{product_id}" in calls
        assert "catalog:search:*" in calls
        assert "catalog:category:*" in calls


class TestCacheIntegration:
    """Pruebas de integración para el cache"""
    
    def test_search_key_casos_especiales(self):
        """Prueba casos especiales en la generación de claves"""
        # Strings vacíos
        key1 = search_key(q="", categoriaId="", codigo="")
        expected1 = "catalog:search:q=|cat=|cod=|pais=|bod=|p=1|s=20|sort="
        assert key1 == expected1
        
        # Valores con espacios
        key2 = search_key(q="medicina con espacios", page=1, size=50)
        expected2 = "catalog:search:q=medicina con espacios|cat=|cod=|pais=|bod=|p=1|s=50|sort="
        assert key2 == expected2
        
        # Caracteres especiales
        key3 = search_key(codigo="MED-001/ABC", pais="CO", sort="precio-asc")
        expected3 = "catalog:search:q=|cat=|cod=MED-001/ABC|pais=CO|bod=|p=1|s=20|sort=precio-asc"
        assert key3 == expected3
    
    @patch('app.cache.get_redis')
    async def test_cache_flujo_completo(self, mock_get_redis):
        """Prueba flujo completo: set -> get -> delete"""
        # Arrange
        mock_redis_client = AsyncMock()
        mock_get_redis.return_value = mock_redis_client
        
        test_key = "test:complete:flow"
        test_data = {"flow": "complete", "items": [1, 2, 3]}
        
        # Configurar mocks
        mock_redis_client.get.return_value = json.dumps(test_data)
        mock_redis_client.keys.return_value = [test_key]
        mock_redis_client.delete.return_value = 1
        
        # Act & Assert
        # 1. Set cache
        await set_cache(test_key, test_data)
        mock_redis_client.setex.assert_called_once()
        
        # 2. Get cache
        result = await get_cache(test_key)
        assert result == test_data
        
        # 3. Delete cache
        deleted = await delete_cache_pattern("test:complete:*")
        assert deleted == 1