import asyncio
from uuid import UUID
from datetime import datetime, timezone

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings
from app.db import SessionLocal
from app.models import OutboxEvent, Order, OrderStatus, IdempotencyRequest, IdemStatus

celery = Celery(__name__,
                broker=settings.CELERY_BROKER_URL,
                backend=settings.CELERY_RESULT_BACKEND)

@celery.task(name="process_outbox_event", max_retries=5, default_retry_delay=5)
def process_outbox_event(event_id: str):
    asyncio.run(_process(event_id))

async def _process(event_id: str):
    async with SessionLocal() as session:  # type: AsyncSession
        # Empieza una transacción explícita
        async with session.begin():
            evt = await session.get(OutboxEvent, UUID(event_id))
            if not evt:
                return

            order = await session.get(Order, evt.aggregate_id)
            if not order:
                return

            # Simula “publicar” el evento (aquí iría Kafka/Rabbit/etc.)
            order.status = OrderStatus.CREATED
            evt.published_at = datetime.now(timezone.utc)

            key_hash = evt.payload["key_hash"]
            idem = await session.get(IdempotencyRequest, key_hash)
            if idem and idem.status != IdemStatus.DONE:
                idem.status = IdemStatus.DONE
                idem.status_code = 201
                idem.response_body = {"order_id": str(order.id), "status": "CREATED"}
        # session.commit() lo hace el context manager de begin()
