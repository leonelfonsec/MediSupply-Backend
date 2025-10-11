# tests/integration/test_orders_happy.py
import app.db as db
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app, _sha256
from app.models import IdempotencyRequest, OutboxEvent, Order

client = TestClient(app)

def test_orders_happy_creates_rows_and_enqueues():
    idem_key = "00000000-0000-0000-0000-000000000010"
    body = {"customer_id": "C-HAPPY", "items": [{"sku": "X1", "qty": 1}]}

    r = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r.status_code in (200, 201, 202)
    data = r.json()
    key_hash = _sha256(idem_key)
    assert data["request_id"] == key_hash

    async def _check():
        # 1) Existe el registro de idempotencia
        async for s in db.get_session():
            idem = await s.get(IdempotencyRequest, key_hash)
            assert idem is not None
            assert idem.status.name in ("PENDING", "DONE")

            # 2) Existe al menos un Order (no asumimos relación directa en IdempotencyRequest)
            res_o = await s.execute(select(Order).limit(1))
            assert res_o.scalar_one_or_none() is not None

            # 3) Existe un OutboxEvent cuyo payload contiene el key_hash
            #    (el payload es texto JSON, así que usamos contains/LIKE)
            res_e = await s.execute(
                select(OutboxEvent).where(OutboxEvent.payload.contains(key_hash))
            )
            evt = res_e.scalar_one_or_none()
            assert evt is not None

    import asyncio
    asyncio.get_event_loop().run_until_complete(_check())

    # 4) Se “envió” la tarea a Celery (dummy del conftest)
    from app import main
    assert any(c[0] == "process_outbox_event" for c in main.celery.calls)
