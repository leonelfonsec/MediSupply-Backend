from fastapi import FastAPI
from app.routes.catalog import router as catalog_router
from app.config import settings
from app.db import engine, Base

app = FastAPI(title="MediSupply Catalog API")
app.include_router(catalog_router, prefix=settings.api_prefix)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
