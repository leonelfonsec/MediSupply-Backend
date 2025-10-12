"""
Modelos SQLAlchemy para cliente-service siguiendo patrón catalogo-service
Definición de tablas para HU07: Consultar Cliente
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, DECIMAL, JSON, Text
from datetime import date, datetime
from decimal import Decimal
from app.db import Base


class Cliente(Base):
    """
    Modelo de Cliente principal
    Representa los clientes del sistema MediSupply
    """
    __tablename__ = "cliente"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nit: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    codigo_unico: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str] = mapped_column(String(32), nullable=True)
    direccion: Mapped[str] = mapped_column(String(512), nullable=True)
    ciudad: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    pais: Mapped[str] = mapped_column(String(8), nullable=True, default="CO")
    # tipo_cliente: Mapped[str] = mapped_column(String(32), nullable=True, default="farmacia")  # Comentado: columna no existe en DB
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompraHistorico(Base):
    """
    Modelo de Histórico de Compras
    Registra todas las compras realizadas por los clientes
    """
    __tablename__ = "compra_historico"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("cliente.id"), nullable=False, index=True)
    orden_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_producto: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False)
    precio_total: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False)
    fecha_compra: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado_orden: Mapped[str] = mapped_column(String(32), nullable=True, default="completada")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DevolucionHistorico(Base):
    """
    Modelo de Histórico de Devoluciones
    Registra todas las devoluciones realizadas por los clientes
    """
    __tablename__ = "devolucion_historico"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("cliente.id"), nullable=False, index=True)
    compra_orden_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad_devuelta: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    categoria_motivo: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    fecha_devolucion: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=True, default="procesada")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConsultaClienteLog(Base):
    """
    Modelo de Log de Consultas
    Para trazabilidad de todas las consultas realizadas (criterio HU07)
    """
    __tablename__ = "consulta_cliente_log"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"LOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now()) % 10000:04d}")
    vendedor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cliente_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tipo_consulta: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tipo_busqueda: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    termino_busqueda: Mapped[str] = mapped_column(String(255), nullable=True)
    took_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    metadatos: Mapped[dict] = mapped_column(JSON, nullable=True)
    fecha_consulta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ProductoPreferido(Base):
    """
    Modelo de Productos Preferidos (vista materializada o tabla calculada)
    Para optimizar consultas de productos preferidos
    """
    __tablename__ = "producto_preferido"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("cliente.id"), nullable=False, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_producto: Mapped[str] = mapped_column(String(128), nullable=True)
    frecuencia_compra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_promedio: Mapped[Decimal] = mapped_column(DECIMAL(8,2), nullable=False, default=0)
    ultima_compra: Mapped[date] = mapped_column(Date, nullable=True)
    meses_desde_ultima_compra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EstadisticaCliente(Base):
    """
    Modelo de Estadísticas del Cliente (vista materializada o tabla calculada)
    Para optimizar consultas de estadísticas resumidas
    """
    __tablename__ = "estadistica_cliente"
    
    cliente_id: Mapped[str] = mapped_column(ForeignKey("cliente.id"), primary_key=True)
    total_compras: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_productos_unicos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_devoluciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_total_compras: Mapped[Decimal] = mapped_column(DECIMAL(15,2), nullable=False, default=0)
    promedio_orden: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False, default=0)
    frecuencia_compra_mensual: Mapped[Decimal] = mapped_column(DECIMAL(8,2), nullable=False, default=0)
    tasa_devolucion: Mapped[Decimal] = mapped_column(DECIMAL(5,2), nullable=False, default=0)
    cliente_desde: Mapped[date] = mapped_column(Date, nullable=True)
    ultima_compra: Mapped[date] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)