from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, DECIMAL
from app.db import Base

class Producto(Base):
    __tablename__ = "producto"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_id: Mapped[str] = mapped_column(String(64), nullable=False)
    presentacion: Mapped[str] = mapped_column(String(128))
    precio_unitario: Mapped[float] = mapped_column(DECIMAL(12,2), nullable=False)
    requisitos_almacenamiento: Mapped[str] = mapped_column(String(128))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class Inventario(Base):
    __tablename__ = "inventario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[str] = mapped_column(ForeignKey("producto.id"), index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    bodega_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lote: Mapped[str] = mapped_column(String(64), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    vence: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    condiciones: Mapped[str] = mapped_column(String(128))
