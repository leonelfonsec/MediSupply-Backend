# tests/integration/test_orders_done_replay.py
import json
import hashlib
import pytest
from sqlalchemy import select, func, delete
from app.models import IdempotencyRequest, IdemStatus, Order, OutboxEvent
from app.schemas import CreateOrderRequest   # <-- NUEVO

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

async def _count(session, model):
    res = await session.execute(select(func.count()).select_from(model))
    return res.scalar_one()

@pytest.mark.anyio
async def test_orders_replay_done_returns_cached_and_no_side_effects(
    client, test_session, override_db, monkeypatch
):
    body = {"customer_id": "C-REPLAY", "items": [{"sku": "X1", "qty": 1}]}

    # usa un key único para este test (o cambia el sufijo)
    idem_key = "00000000-0000-0000-0000-00000000D0NE-1"
    key_hash = _sha256(idem_key)

    # hashea igual que el endpoint
    req_model = CreateOrderRequest(**body)
    body_hash = _sha256(req_model.model_dump_json())

    # 🔧 limpia cualquier residuo previo con el mismo key_hash
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    cached_body = {"request_id": key_hash, "message": "Ya procesado (idempotente)"}

    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=body_hash,
        status=IdemStatus.DONE,
        response_body=json.dumps(cached_body),
    )
    test_session.add(idem)
    await test_session.flush()

    orders_before = await _count(test_session, Order)
    outbox_before = await _count(test_session, OutboxEvent)
    await test_session.commit()  # que sea visible para la sesión del request

    calls = {"n": 0}
    def fake_send_task(*args, **kwargs):
        calls["n"] += 1
    monkeypatch.setattr("app.main.celery.send_task", fake_send_task, raising=True)

    r = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r.status_code == 202
    assert r.json() == cached_body

    orders_after = await _count(test_session, Order)
    outbox_after = await _count(test_session, OutboxEvent)
    assert orders_before == orders_after
    assert outbox_before == outbox_after
    assert calls["n"] == 0