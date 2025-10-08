import aioredis
from app.config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis

def search_key(q=None, categoriaId=None, codigo=None, pais=None, bodegaId=None, page=1, size=20, sort=None):
    parts = [f"q={q or ''}", f"cat={categoriaId or ''}", f"cod={codigo or ''}", f"pais={pais or ''}",
             f"bod={bodegaId or ''}", f"p={page}", f"s={size}", f"sort={sort or ''}"]
    return "catalog:search:" + "|".join(parts)
