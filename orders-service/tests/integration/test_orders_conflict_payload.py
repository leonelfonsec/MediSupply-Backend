import pytest
import hashlib
from sqlalchemy import delete
from app.models import IdempotencyRequest, IdemStatus
from app.schemas import CreateOrderRequest

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

@pytest.mark.anyio
async def test_orders_conflict_same_key_different_payload_returns_409(
    client, test_session, override_db
):
    idem_key = "00000000-0000-0000-0000-00000000C0NF-1"
    key_hash = _sha256(idem_key)

    original_body = {"customer_id": "C-ONE", "items": [{"sku": "A", "qty": 1}]}
    original_req = CreateOrderRequest(**original_body)
    original_hash = _sha256(original_req.model_dump_json())

    # Limpia si quedó residuo
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    # Prepara idem existente (PENDING) con primer payload
    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=original_hash,
        status=IdemStatus.PENDING,
        response_body=None,
    )
    test_session.add(idem)
    await test_session.commit()

    # Mismo Idempotency-Key pero payload DIFERENTE -> 409
    different_body = {"customer_id": "C-OTHER", "items": [{"sku": "B", "qty": 2}]}
    r = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=different_body)
    assert r.status_code == 409
    assert r.json()["detail"] == "Idempotency-Key ya usada con payload distinto"
