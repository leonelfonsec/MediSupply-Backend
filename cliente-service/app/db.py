"""
Configuración de base de datos para cliente-service
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from typing import AsyncGenerator
from app.config import settings

# Base para los modelos
Base = declarative_base()

# Engine asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Crear todas las tablas de la base de datos
    """
    # Importar modelos para registrarlos
    from app.models import (
        Cliente, CompraHistorico, DevolucionHistorico, 
        ConsultaClienteLog, ProductoPreferido, EstadisticaCliente, Base
    )
    
    async with engine.begin() as conn:
        # Crear todas las tablas
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tablas de cliente-service creadas correctamente")


async def drop_tables():
    """
    Eliminar todas las tablas (para testing)
    """
    from app.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)