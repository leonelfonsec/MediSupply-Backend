import redis.asyncio as redis
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)
_redis = None

async def get_redis():
    """Obtiene una conexión a Redis reutilizable."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis

def search_key(q=None, categoriaId=None, codigo=None, pais=None, bodegaId=None, page=1, size=20, sort=None):
    """Genera clave de caché para búsquedas."""
    parts = [f"q={q or ''}", f"cat={categoriaId or ''}", f"cod={codigo or ''}", f"pais={pais or ''}",
             f"bod={bodegaId or ''}", f"p={page}", f"s={size}", f"sort={sort or ''}"]
    return "catalog:search:" + "|".join(parts)

async def set_cache(key: str, data: dict, ttl: int = 300):
    """
    Guarda datos en caché con TTL especificado.
    
    Args:
        key: Clave de caché
        data: Datos a guardar (serializables a JSON)
        ttl: Tiempo de vida en segundos (default: 5 minutos)
    """
    try:
        redis_client = await get_redis()
        json_data = json.dumps(data)
        await redis_client.setex(key, ttl, json_data)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")

async def get_cache(key: str):
    """
    Obtiene datos del caché.
    
    Args:
        key: Clave de caché
        
    Returns:
        dict | None: Datos deserializados o None si no existe o hay error
    """
    try:
        redis_client = await get_redis()
        json_data = await redis_client.get(key)
        if json_data:
            logger.debug(f"Cache hit: {key}")
            return json.loads(json_data)
        else:
            logger.debug(f"Cache miss: {key}")
            return None
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
        return None

async def delete_cache_pattern(pattern: str) -> int:
    """
    Elimina claves de caché que coincidan con el patrón.
    
    Args:
        pattern: Patrón de búsqueda (ej: "catalog:search:*")
        
    Returns:
        int: Número de claves eliminadas
    """
    try:
        redis_client = await get_redis()
        keys = await redis_client.keys(pattern)
        if keys:
            deleted = await redis_client.delete(*keys)
            logger.debug(f"Cache delete pattern {pattern}: {deleted} keys removed")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"Cache delete pattern error for {pattern}: {e}")
        return 0

async def invalidate_product_cache(product_id: str = None):
    """
    Invalida caché relacionado con productos.
    
    Args:
        product_id: ID del producto específico (opcional)
    """
    patterns = [
        "catalog:search:*",  # Todas las búsquedas
        "catalog:category:*",  # Todas las categorías  
    ]
    
    if product_id:
        patterns.append(f"catalog:product:{product_id}")
    
    total_deleted = 0
    for pattern in patterns:
        deleted = await delete_cache_pattern(pattern)
        total_deleted += deleted
    
    logger.info(f"Product cache invalidated: {total_deleted} keys removed")
    return total_deleted
