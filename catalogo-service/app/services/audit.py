import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

async def audit_log(session: AsyncSession, *, user_id: str | None, endpoint: str, filtros: dict, took_ms: int, canal: str):
    # Tabla sencilla de auditoría (se crea en la migración)
    await session.execute(
        text("INSERT INTO consulta_catalogo_log(user_id, endpoint, filtros, took_ms, canal) VALUES (:u,:e,:f::jsonb,:t,:c)"),
        {"u": user_id, "e": endpoint, "f": json.dumps(filtros), "t": took_ms, "c": canal}
    )
    await session.commit()
