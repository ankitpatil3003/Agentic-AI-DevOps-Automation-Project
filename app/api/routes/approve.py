# app/api/routes/approve.py

from fastapi import APIRouter, HTTPException
from requests import HTTPError

from app.core.task_store import task_store
from app.integrations.servicenow_client import ServiceNowClient
from app.agents.incident_report_agent import IncidentReportAgent
from app.workflows.coordinator_graph import run_agentic_flow

router = APIRouter(prefix="/api/v1", tags=["v1"])

_PREFIX = "[AUTOMATION REQUEST]"

def _extract_request_from_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    return t[len(_PREFIX):].strip() if t.lower().startswith(_PREFIX.lower()) else t


@router.post("/plans/{id}/approve")
async def approve_plan(id: str):
    """
    Approve a pending plan and resume execution:
      1) verify incident exists
      2) reconstruct original request from description/short_description
      3) post approval note
      4) run agentic flow (diagnose/script/email -> resolve)
      5) persist 'completed' to task_store
    """
    # Optional: enforce waiting_approval only if the store has an entry
    plan_entry = task_store.get(id)
    if plan_entry and plan_entry.get("status") not in {"waiting_approval", "awaiting_approval"}:
        raise HTTPException(status_code=400, detail="Plan is not awaiting approval.")

    try:
        inc = ServiceNowClient.get_incident(id)  # Table API read by sys_id
    except HTTPError as e:
        raise HTTPException(status_code=404, detail=f"Incident not found or not accessible: {e}") from e

    # Prefer long description; fall back to short_description
    user_request = (
        _extract_request_from_text(inc.get("description") or "")
        or _extract_request_from_text(inc.get("short_description") or "")
        or "Run diagnostic & remediation and produce a summary email."
    )

    IncidentReportAgent.post_note(id, "Approval received. Executing agentic plan.")

    # Execute; inside it we PATCH by sys_id and finally resolve with resolution fields.
    result = run_agentic_flow(id, user_request)

    # Persist terminal state so /tasks reflects completion immediately
    task_store[id] = {"status": "completed", **result}

    return {
        "incident_sys_id": id,
        "status": result.get("status", "completed"),
        "diagnosis": result.get("diagnosis"),
        "script": result.get("script"),
        "email_draft": result.get("email_draft"),
        "servicenow_updated": result.get("servicenow_updated", True),
    }
