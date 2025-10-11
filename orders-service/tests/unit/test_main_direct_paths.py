import json
import hashlib
import pytest
from sqlalchemy import select, func, delete

from app.main import create_order, _sha256   # llamamos la función directamente
from app.models import IdempotencyRequest, IdemStatus, Order, OutboxEvent
from app.schemas import CreateOrderRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

async def _count(session, model):
    from sqlalchemy import select, func
    res = await session.execute(select(func.count()).select_from(model))
    return res.scalar_one()

@pytest.mark.anyio
async def test_direct_pending_same_body_enters_try_and_creates_order(test_session, monkeypatch):
    body = {"customer_id": "C-PEND-DIRECT", "items": [{"sku": "PD1", "qty": 1}]}
    req = CreateOrderRequest(**body)
    body_hash = _sha256(req.model_dump_json())

    idem_key = "00000000-0000-0000-0000-00000000PEND-DIR"
    key_hash = h(idem_key)

    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    idem = IdempotencyRequest(
        key_hash=key_hash, body_hash=body_hash, status=IdemStatus.PENDING
    )
    test_session.add(idem)
    await test_session.commit()

    before_o = await _count(test_session, Order)
    before_e = await _count(test_session, OutboxEvent)

    calls = {"n": 0}
    monkeypatch.setattr(
        "app.main.celery.send_task",
        lambda *a, **k: calls.update(n=calls["n"] + 1),
        raising=True,
    )

    # ⬇️ Usa una sesión NUEVA para llamar a create_order
    Session = async_sessionmaker(bind=test_session.bind, expire_on_commit=False, class_=AsyncSession)
    async with Session() as fresh_session:
        resp = await create_order(
            body=req,
            Idempotency_Key=idem_key,
            session=fresh_session,
        )

    assert resp.request_id == key_hash

    after_o = await _count(test_session, Order)
    after_e = await _count(test_session, OutboxEvent)
    assert after_o == before_o + 1
    assert after_e == before_e + 1
    assert calls["n"] == 1

@pytest.mark.anyio
async def test_direct_done_returns_cached_early_return(test_session, monkeypatch):
    """
    Cubre: rama DONE + response_body (líneas 48–49) => return temprano.
    """
    body = {"customer_id": "C-DONE-DIRECT", "items": [{"sku": "D1", "qty": 1}]}
    req = CreateOrderRequest(**body)
    body_hash = _sha256(req.model_dump_json())

    idem_key = "00000000-0000-0000-0000-00000000D0NE-DIR"
    key_hash = h(idem_key)
    cached = {"request_id": key_hash, "message": "Ya procesado (idempotente)"}

    await test_session.execute(delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash))
    await test_session.commit()

    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=body_hash,
        status=IdemStatus.DONE,
        response_body=json.dumps(cached),
    )
    test_session.add(idem)
    await test_session.commit()

    # defensivo: si la función intentara encolar, lo veríamos
    calls = {"n": 0}
    monkeypatch.setattr("app.main.celery.send_task",
                        lambda *a, **k: calls.update(n=calls["n"] + 1),
                        raising=True)

    resp = await create_order(
        body=req,
        Idempotency_Key=idem_key,
        session=test_session,
    )
    assert resp.request_id == key_hash
    # exactamente la respuesta cacheada
    assert resp.model_dump() == cached
    assert calls["n"] == 0  # no se encola en replay

@pytest.mark.anyio
async def test_direct_conflict_same_key_different_payload_raises_409(test_session):
    """
    Cubre: raise HTTPException(409) (línea 46).
    """
    body1 = {"customer_id": "C1", "items": [{"sku": "A", "qty": 1}]}
    body2 = {"customer_id": "C2", "items": [{"sku": "B", "qty": 2}]}

    req1 = CreateOrderRequest(**body1)
    req2 = CreateOrderRequest(**body2)
    bh1 = _sha256(req1.model_dump_json())

    idem_key = "00000000-0000-0000-0000-00000000C0NF-DIR"
    key_hash = h(idem_key)

    await test_session.execute(delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash))
    await test_session.commit()

    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=bh1,
        status=IdemStatus.PENDING
    )
    test_session.add(idem)
    await test_session.commit()

    with pytest.raises(Exception) as ex:
        await create_order(
            body=req2,  # payload distinto
            Idempotency_Key=idem_key,
            session=test_session,
        )
    # FastAPI levanta HTTPException; en test directo aceptamos cualquier Exception pero
    # comprobamos que el detalle es el esperado.
    assert "Idempotency-Key ya usada con payload distinto" in str(ex.value)
