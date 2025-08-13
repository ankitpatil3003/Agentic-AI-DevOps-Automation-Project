# tests/test_agent_retry.py

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.agents import automation_agent

client = TestClient(app)


def test_agent_retry(monkeypatch):
    # Simulate AutomationAgent failure
    def fail_script_gen(request_text: str):
        raise RuntimeError("Script generation failed.")

    monkeypatch.setattr(automation_agent.AutomationAgent, "run", fail_script_gen)

    payload = {
        "request": "Diagnose network slowness and generate a fix script.",
        "require_approval": False
    }

    response = client.post("/api/v1/execute", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "resolved"

    # Diagnosis should still be present
    assert "diagnosis" in data

    # Script might be missing or incomplete due to error
    assert "script" not in data or data["script"] is None or data["script"]["lint_passed"] is False
