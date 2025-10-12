import uuid
import enum
from sqlalchemy import Column, String, Enum, JSON, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from enum import Enum as PyEnum

from app.db import Base

# --- ENUM de OrderStatus (controlado por metadata) ---
class OrderStatus(PyEnum):
    NEW = "NEW"
    CREATED = "CREATED"
    FAILED = "FAILED"

# 🔹 ENUM idempotente: SQLAlchemy lo registra y usa checkfirst internamente
orderstatus_enum = ENUM(
    OrderStatus,
    name="orderstatus",
    metadata=Base.metadata,    # <- lo gestiona el mismo Base
    create_type=True,          # crea si no existe
    validate_strings=True
)


# --- ENUM de IdemStatus ---
class IdemStatus(PyEnum):
    PENDING = "PENDING"
    DONE = "DONE"


# --- MODELOS ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)
    items = Column(JSON, nullable=False)
    status = Column(orderstatus_enum, nullable=False, default=OrderStatus.NEW)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IdempotencyRequest(Base):
    __tablename__ = "idempotency_requests"

    key_hash = Column(String, primary_key=True)
    body_hash = Column(String, nullable=False)
    status = Column(
        Enum(IdemStatus, name="idemstatus", metadata=Base.metadata, create_type=True),
        nullable=False,
        default=IdemStatus.PENDING,
    )
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    type = Column(String, nullable=False)  # e.g., "OrderCreated"
    payload = Column(JSON, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retries = Column(Integer, nullable=False, default=0)
