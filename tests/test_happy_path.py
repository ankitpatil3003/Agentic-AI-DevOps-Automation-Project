# tests/test_happy_path.py
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_happy_path():
    req_payload = {
        "request": "Diagnose high CPU usage on VM-node1 and generate a mitigation script.",
        "require_approval": False,
    }
    resp = client.post("/api/v1/execute", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("completed", "resolved")  # accept either
    assert "diagnosis" in data
    assert "script" in data
    assert "email_draft" in data
    assert data.get("servicenow_updated") is True
