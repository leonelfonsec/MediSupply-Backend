from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Producto, Inventario
from typing import Optional

async def buscar_productos(session: AsyncSession, *,
                           q: Optional[str], categoriaId: Optional[str], codigo: Optional[str],
                           pais: Optional[str], bodegaId: Optional[str],
                           page: int, size: int, sort: Optional[str]):

    stmt = select(Producto).where(Producto.activo.is_(True))
    if q:
        stmt = stmt.where(func.lower(Producto.nombre).like(f"%{q.lower()}%"))
    if categoriaId:
        stmt = stmt.where(Producto.categoria_id == categoriaId)
    if codigo:
        stmt = stmt.where(Producto.codigo == codigo)

    # Orden
    if sort == "precio":
        stmt = stmt.order_by(Producto.precio_unitario.asc())
    else:
        stmt = stmt.order_by(Producto.nombre.asc())

    total = (await session.execute(stmt.with_only_columns(func.count()))).scalar_one()
    rows = (await session.execute(stmt.offset((page-1)*size).limit(size))).scalars().all()

    # inventario resumen (agregado por SKU)
    ids = [r.id for r in rows]
    if not ids:
        return rows, 0, []

    inv = select(
        Inventario.producto_id,
        func.sum(Inventario.cantidad).label("cantidad"),
        func.array_agg(func.distinct(Inventario.pais)).label("paises")
    ).where(Inventario.producto_id.in_(ids))
    if pais:
        inv = inv.where(Inventario.pais == pais)
    if bodegaId:
        inv = inv.where(Inventario.bodega_id == bodegaId)
    inv = inv.group_by(Inventario.producto_id)

    inv_rows = (await session.execute(inv)).all()
    inv_map = {r.producto_id: {"cantidad": int(r.cantidad or 0), "paises": list(r.paises or [])} for r in inv_rows}
    return rows, total, inv_map

async def detalle_inventario(session: AsyncSession, producto_id: str, page:int, size:int):
    base = select(Inventario).where(Inventario.producto_id == producto_id)
    total = (await session.execute(base.with_only_columns(func.count()))).scalar_one()
    rows = (await session.execute(base.order_by(Inventario.vence.asc())
                        .offset((page-1)*size).limit(size))).scalars().all()
    return rows, total
