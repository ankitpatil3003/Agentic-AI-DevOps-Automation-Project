# tests/test_approval_flow.py

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.task_store import task_store

client = TestClient(app)


def test_approval_flow():
    req_payload = {
        "request": "Limit inbound RDP traffic on production VMs to 10.0.0.0/24",
        "require_approval": True
    }

    # Step 1: Execute request with approval = true
    execute_resp = client.post("/api/v1/execute", json=req_payload)
    assert execute_resp.status_code == 200
    data = execute_resp.json()

    assert data["status"] == "waiting_approval"
    assert "incident_sys_id" in data
    sys_id = data["incident_sys_id"]

    # Step 2: Approve it
    approve_resp = client.post(f"/api/v1/plans/{sys_id}/approve")
    assert approve_resp.status_code == 200
    result = approve_resp.json()

    assert result["status"] == "completed" or result["status"] == "resolved"
    assert "diagnosis" in result
    assert "script" in result
    assert "email_draft" in result
