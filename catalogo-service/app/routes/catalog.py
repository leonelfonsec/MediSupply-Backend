from fastapi import APIRouter, Depends, Query, Request
from app.db import get_session
from app.cache import get_redis, search_key
from app.schemas import SearchResponse, Product, Meta, StockItem
from app.repositories.catalog_repo import buscar_productos, detalle_inventario
from app.config import settings
import time, orjson

router = APIRouter(prefix="/catalog", tags=["catalog"])

@router.get("/items", response_model=SearchResponse)
async def list_items(
    request: Request,
    q: str | None = None,
    categoriaId: str | None = None,
    codigo: str | None = None,
    pais: str | None = None,
    bodegaId: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(settings.page_size_default, ge=1, le=settings.page_size_max),
    sort: str | None = Query(None, pattern="^(relevancia|precio|cantidad|vencimiento)?$"),
    session = Depends(get_session)
):
    started = time.perf_counter_ns()
    redis = await get_redis()
    key = search_key(q, categoriaId, codigo, pais, bodegaId, page, size, sort)

    cached = await redis.get(key)
    if cached:
        payload = orjson.loads(cached)
        return payload

    rows, total, inv_map = await buscar_productos(session, q=q, categoriaId=categoriaId, codigo=codigo,
                                                  pais=pais, bodegaId=bodegaId, page=page, size=size, sort=sort)
    items = []
    for r in rows:
        res = {
            "id": r.id,
            "nombre": r.nombre,
            "codigo": r.codigo,
            "categoria": r.categoria_id,
            "presentacion": r.presentacion,
            "precioUnitario": float(r.precio_unitario),
            "requisitosAlmacenamiento": r.requisitos_almacenamiento,
        }
        if r.id in inv_map:
            res["inventarioResumen"] = {
                "cantidadTotal": inv_map[r.id]["cantidad"],
                "paises": inv_map[r.id]["paises"]
            }
        items.append(res)

    took_ms = int((time.perf_counter_ns() - started)/1_000_000)
    payload = {"items": items, "meta": {"page": page, "size": size, "total": total, "tookMs": took_ms}}
    # cache 5s
    await redis.setex(key, 5, orjson.dumps(payload))  # TTL 5s
    return payload

@router.get("/items/{id}")
async def get_product(id: str, session=Depends(get_session)):
    # …consulta sencilla por id (similar al repo)
    from sqlalchemy import select
    from app.models.catalogo_model import Producto
    row = (await session.execute(select(Producto).where(Producto.id==id))).scalar_one_or_none()
    if not row:
        return {"detail":"Not found"}, 404
    return {
        "id": row.id, "nombre": row.nombre, "codigo": row.codigo, "categoria": row.categoria_id,
        "presentacion": row.presentacion, "precioUnitario": float(row.precio_unitario),
        "requisitosAlmacenamiento": row.requisitos_almacenamiento
    }

@router.get("/items/{id}/inventario")
async def get_inventory(id: str, page:int=1, size:int=50, session=Depends(get_session)):
    rows, total = await detalle_inventario(session, id, page, size)
    items = [{
        "pais": r.pais, "bodegaId": r.bodega_id, "lote": r.lote,
        "cantidad": r.cantidad, "vence": r.vence.isoformat(), "condiciones": r.condiciones
    } for r in rows]
    return {"items": items, "meta": {"page": page, "size": size, "total": total, "tookMs": 0}}
