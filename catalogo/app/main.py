from fastapi import FastAPI
from app.routes.catalog import router as catalog_router
from app.config import settings

app = FastAPI(title="MediSupply Catalog API", default_response_class=None)
app.include_router(catalog_router, prefix=settings.api_prefix)
