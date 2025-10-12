from fastapi import FastAPI
from app.routes.client import router as cliente_router
from app.config import settings
from app.db import engine, Base

app = FastAPI(title="MediSupply Cliente API")
app.include_router(cliente_router, prefix=settings.api_prefix)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)