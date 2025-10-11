import uuid, enum
from sqlalchemy import Column, String, Enum, JSON, Integer, Text, func, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from app.db import Base

class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    CREATED = "CREATED"
    FAILED = "FAILED"

class IdemStatus(str, enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"

class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)
    items = Column(JSON, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.NEW)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IdempotencyRequest(Base):
    __tablename__ = "idempotency_requests"
    key_hash = Column(String, primary_key=True)  # sha256 de la key
    body_hash = Column(String, nullable=False)
    status = Column(Enum(IdemStatus), nullable=False, default=IdemStatus.PENDING)
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
