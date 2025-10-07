from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.settings import settings
from sqlalchemy.orm import declarative_base

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True, 
    future=True,
    pool_size=15,
    max_overflow=25,
    pool_timeout=30,
    pool_recycle=3600
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_session() -> AsyncSession:
    async with SessionLocal() as s:
        yield s
