from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.settings import settings
import os

Base = declarative_base()

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=os.getenv("SQLA_ECHO", "0") == "1",
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncSession:
    async with SessionLocal() as s:
        yield s
