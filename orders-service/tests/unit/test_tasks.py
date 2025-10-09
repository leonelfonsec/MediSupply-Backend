# tests/unit/test_tasks.py
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.tasks as tasks
from app.models import OutboxEvent, Order, OrderStatus, IdempotencyRequest, IdemStatus

def _patch_sessionlocal_to_test_engine(test_engine, monkeypatch):
    Session = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)
    monkeypatch.setattr(tasks, "SessionLocal", Session, raising=True)

# 1) TEST SÍNCRONO -> Cubre process_outbox_event() (líneas 16–18) y early return si no hay evento
def test_tasks_missing_event_returns_early_sync(test_engine, monkeypatch):
    _patch_sessionlocal_to_test_engine(test_engine, monkeypatch)
    random_id = str(uuid.uuid4())
    # No hay event loop corriendo, asyncio.run() funciona y no debe lanzar
    tasks.process_outbox_event(random_id)

# 2) TEST ASYNC -> rama: evento existe pero el Order NO (early return en _process)
@pytest.mark.anyio
async def test_tasks_event_present_but_order_missing_returns_early(
    test_engine, test_session, monkeypatch
):
    _patch_sessionlocal_to_test_engine(test_engine, monkeypatch)

    # ⬇️ usar UUID real en aggregate_id
    missing_order_id = uuid.uuid4()  # ✅ UUID real

    evt = OutboxEvent(
        aggregate_id=missing_order_id,         # ✅ UUID, no str
        type="OrderCreated",
        payload={"order_id": "no-order", "key_hash": "kh-missing"},
    )
    test_session.add(evt)
    await test_session.flush()
    event_uuid = getattr(evt, "event_id", None) or getattr(evt, "id")
    await test_session.commit()

    await tasks._process(str(event_uuid))      # _process espera un str convertible a UUID

    got = await test_session.get(OutboxEvent, event_uuid)
    assert got.published_at is None

# 3) TEST ASYNC -> happy path: marca Order CREATED + Idempotency DONE + published_at
@pytest.mark.anyio
async def test_tasks_happy_flow_updates_order_and_idempotency(
    test_engine, test_session, monkeypatch
):
    _patch_sessionlocal_to_test_engine(test_engine, monkeypatch)

    order = Order(customer_id="C-TASK", items=[{"sku": "X1", "qty": 1}])
    test_session.add(order)
    await test_session.flush()

    key_hash = f"kh-{uuid.uuid4().hex}"   # en lugar de "kh-ok"
    idem = IdempotencyRequest(key_hash=key_hash, body_hash="bh", status=IdemStatus.PENDING)
    test_session.add(idem)
    await test_session.flush()

    evt = OutboxEvent(
        aggregate_id=order.id,
        type="OrderCreated",
        payload={"order_id": str(order.id), "key_hash": key_hash},
    )
    test_session.add(evt)
    await test_session.flush()

    event_uuid = evt.event_id            # ✅ existe siempre
    await test_session.commit()

    await tasks._process(str(event_uuid))

    # Lee objetos y refresca
    o = await test_session.get(Order, order.id)
    e = await test_session.get(OutboxEvent, event_uuid)
    i = await test_session.get(IdempotencyRequest, key_hash)

    await test_session.refresh(o)
    await test_session.refresh(e)
    await test_session.refresh(i)

    assert o.status == OrderStatus.CREATED
    assert e.published_at is not None
    assert i.status == IdemStatus.DONE
    assert i.status_code == 201
    assert i.response_body == {"order_id": str(order.id), "status": "CREATED"}
