# tests/test_rejection_flow.py

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.task_store import task_store

client = TestClient(app)


def test_rejection_flow():
    # Step 1: Submit request with approval required
    payload = {
        "request": "Block SSH access on all production servers.",
        "require_approval": True
    }

    response = client.post("/api/v1/execute", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "waiting_approval"
    incident_sys_id = data["incident_sys_id"]

    # Step 2: Reject the plan
    reject_resp = client.post(f"/api/v1/plans/{incident_sys_id}/reject")
    assert reject_resp.status_code == 200

    result = reject_resp.json()
    assert result["status"] == "manual_intervention_required"
    assert "message" in result
