import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from faker import Faker
import json
import fakeredis
from app.cache import get_redis, set_cache, get_cache, delete_cache_pattern
from tests.factories import generate_test_productos

fake = Faker(['es_ES'])

class TestCacheOperations:
    """Pruebas para operaciones de caché Redis."""

    @pytest.mark.unit
    async def test_get_redis_connection(self, fake_redis):
        """Prueba obtener conexión a Redis."""
        with patch('app.cache.redis_client', fake_redis):
            # Act
            redis_conn = get_redis()
            
            # Assert
            assert redis_conn is not None
            # Probar que funciona
            await redis_conn.set("test_key", "test_value")
            value = await redis_conn.get("test_key")
            assert value == "test_value"

    @pytest.mark.unit
    async def test_set_cache_basico(self, fake_redis):
        """Prueba guardar en caché."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange
            test_data = {"productos": [{"id": "1", "nombre": "Test"}]}
            cache_key = "test_products"
            
            # Act
            await set_cache(cache_key, test_data, 300)
            
            # Assert
            cached_value = await fake_redis.get(cache_key)
            assert cached_value is not None
            cached_data = json.loads(cached_value)
            assert cached_data == test_data

    @pytest.mark.unit
    async def test_set_cache_con_expiracion(self, fake_redis):
        """Prueba caché con tiempo de expiración."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange
            test_data = {"temp": "data"}
            cache_key = "temp_key"
            
            # Act
            await set_cache(cache_key, test_data, 1)  # 1 segundo
            
            # Assert
            ttl = await fake_redis.ttl(cache_key)
            assert ttl > 0  # Debería tener TTL configurado

    @pytest.mark.unit
    async def test_get_cache_existente(self, fake_redis):
        """Prueba obtener datos existentes del caché."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange
            test_data = {"cached": "data"}
            cache_key = "existing_key"
            await fake_redis.set(cache_key, json.dumps(test_data))
            
            # Act
            result = await get_cache(cache_key)
            
            # Assert
            assert result == test_data

    @pytest.mark.unit
    async def test_get_cache_no_existente(self, fake_redis):
        """Prueba obtener datos no existentes del caché."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Act
            result = await get_cache("non_existent_key")
            
            # Assert
            assert result is None

    @pytest.mark.unit
    async def test_delete_cache_pattern_simple(self, fake_redis):
        """Prueba eliminar caché por patrón simple."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange
            await fake_redis.set("catalog:products:1", "data1")
            await fake_redis.set("catalog:products:2", "data2")
            await fake_redis.set("other:key", "data3")
            
            # Act
            deleted_count = await delete_cache_pattern("catalog:products:*")
            
            # Assert
            assert deleted_count >= 2
            
            # Verificar que se eliminaron las claves correctas
            remaining = await fake_redis.get("other:key")
            assert remaining is not None

    @pytest.mark.unit
    async def test_delete_cache_pattern_complejo(self, fake_redis):
        """Prueba eliminar caché con patrón complejo."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange - Simular claves de productos con diferentes filtros
            cache_keys = [
                "catalog:search:amoxicilina:page1",
                "catalog:search:ibuprofeno:page1", 
                "catalog:search:amoxicilina:page2",
                "catalog:category:ANTIBIOTICS",
                "user:session:123"
            ]
            
            for key in cache_keys:
                await fake_redis.set(key, f"data_{key}")
            
            # Act - Eliminar solo búsquedas de amoxicilina
            deleted = await delete_cache_pattern("catalog:search:amoxicilina:*")
            
            # Assert
            assert deleted >= 2
            
            # Verificar que otros datos no se eliminaron
            ibuprofeno_data = await fake_redis.get("catalog:search:ibuprofeno:page1")
            assert ibuprofeno_data is not None

class TestCacheStrategies:
    """Pruebas para estrategias de caché."""

    @pytest.mark.unit
    async def test_cache_key_generation_busqueda(self):
        """Prueba generación de claves para búsquedas."""
        # Las claves de caché deberían ser consistentes
        params1 = {"q": "amoxicilina", "page": 1, "size": 20}
        params2 = {"page": 1, "size": 20, "q": "amoxicilina"}  # Orden diferente
        
        # Simular generación de clave (esto iría en cache.py)
        def generate_cache_key(prefix, **params):
            sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{prefix}:{sorted_params}"
        
        key1 = generate_cache_key("search", **params1)
        key2 = generate_cache_key("search", **params2)
        
        assert key1 == key2  # Deberían ser iguales independiente del orden

    @pytest.mark.unit
    async def test_cache_invalidation_producto_actualizado(self, fake_redis):
        """Prueba invalidación cuando se actualiza un producto."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange - Simular caché de búsquedas que incluyen un producto
            producto_id = "PROD123"
            search_caches = [
                f"catalog:search:amoxicilina:page1",
                f"catalog:search:antibiotico:page1",
                f"catalog:category:ANTIBIOTICS",
                f"catalog:product:{producto_id}"
            ]
            
            for cache_key in search_caches:
                await fake_redis.set(cache_key, f"cached_data_{cache_key}")
            
            # Act - Invalidar caché relacionado con producto
            # Esto simularía lo que pasaría cuando se actualiza un producto
            patterns_to_invalidate = [
                "catalog:search:*",  # Todas las búsquedas
                "catalog:category:*",  # Todas las categorías
                f"catalog:product:{producto_id}"  # El producto específico
            ]
            
            total_deleted = 0
            for pattern in patterns_to_invalidate:
                deleted = await delete_cache_pattern(pattern)
                total_deleted += deleted
            
            # Assert
            assert total_deleted >= len(search_caches)

    @pytest.mark.unit
    async def test_cache_con_datos_faker(self, fake_redis):
        """Prueba caché con datos generados por Faker."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange
            productos_fake = generate_test_productos(5)
            
            # Convertir a formato serializable
            productos_data = []
            for p in productos_fake:
                productos_data.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "categoria": p.categoria_id,
                    "precio": float(p.precio_unitario),
                    "descripcion": p.descripcion
                })
            
            cache_data = {
                "productos": productos_data,
                "total": len(productos_data),
                "generated_at": fake.iso8601()
            }
            
            # Act
            await set_cache("test_productos_faker", cache_data, 300)
            retrieved_data = await get_cache("test_productos_faker")
            
            # Assert
            assert retrieved_data is not None
            assert retrieved_data["total"] == 5
            assert len(retrieved_data["productos"]) == 5
            
            # Verificar estructura de productos
            for producto in retrieved_data["productos"]:
                assert "id" in producto
                assert "nombre" in producto
                assert "precio" in producto
                assert isinstance(producto["precio"], (int, float))

class TestCacheErrors:
    """Pruebas para manejo de errores en caché."""

    @pytest.mark.unit
    async def test_cache_redis_connection_error(self):
        """Prueba manejo de error de conexión a Redis."""
        with patch('app.cache.get_redis') as mock_get_redis:
            # Arrange
            mock_redis = AsyncMock()
            mock_redis.set.side_effect = ConnectionError("Redis not available")
            mock_get_redis.return_value = mock_redis
            
            # Act & Assert - No debería lanzar excepción
            try:
                await set_cache("test_key", {"data": "test"}, 300)
                # Si llegamos aquí, significa que el error se manejó correctamente
                success = True
            except Exception:
                success = False
            
            assert success  # El método debería manejar el error silenciosamente

    @pytest.mark.unit
    async def test_cache_json_serialization_error(self, fake_redis):
        """Prueba manejo de error de serialización JSON."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange - Objeto no serializable
            non_serializable_data = {"func": lambda x: x}
            
            # Act & Assert
            try:
                await set_cache("test_key", non_serializable_data, 300)
                success = False  # No debería llegar aquí
            except (TypeError, ValueError):
                success = True  # Error esperado
            
            assert success

    @pytest.mark.unit  
    async def test_cache_get_json_decode_error(self, fake_redis):
        """Prueba manejo de error al decodificar JSON corrupto."""
        with patch('app.cache.get_redis', return_value=fake_redis):
            # Arrange - Guardar datos corruptos directamente
            await fake_redis.set("corrupt_key", "invalid json data {")
            
            # Act
            result = await get_cache("corrupt_key")
            
            # Assert - Debería retornar None en caso de error
            assert result is None