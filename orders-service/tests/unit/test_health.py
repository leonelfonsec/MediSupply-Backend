from fastapi.testclient import TestClient
from app.main import app


def test_root():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
