# app/api/routes/reject.py

from fastapi import APIRouter, HTTPException
from requests import HTTPError

from app.core.task_store import task_store
from app.agents.incident_report_agent import IncidentReportAgent
from app.integrations.servicenow_client import ServiceNowClient

# Keep routes grouped and documented under /api/v1
router = APIRouter(prefix="/api/v1", tags=["v1"])

@router.post("/plans/{id}/reject")
async def reject_plan(id: str):
    """
    Reject a pending automation plan (id must be the incident sys_id).
    Behavior:
      - Validates the incident exists by sys_id (Table API read)
      - Posts a work note and leaves the incident open for humans
      - Persists status in task_store so GET /api/v1/tasks/{id} shows
        'manual_intervention_required' immediately
    """
    # 1) Verify the incident exists (read by sys_id is the canonical pattern)
    try:
        _ = ServiceNowClient.get_incident(id)
    except HTTPError as e:
        raise HTTPException(status_code=404, detail=f"Incident not found or not accessible: {e}") from e

    # 2) Check any stored plan state (if present)
    plan_entry = task_store.get(id)
    if plan_entry and plan_entry.get("status") not in {"waiting_approval", "awaiting_approval"}:
        raise HTTPException(status_code=400, detail="Plan is not waiting for approval.")

    # 3) Post note & keep incident open for human follow-up
    try:
        # This method should add a work_note and set state=1 (New) or leave as-is.
        IncidentReportAgent.mark_manual_intervention(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark manual intervention: {e}")

    # 4) Persist terminal status in your local store so /tasks reflects it
    task_store[id] = {
        "status": "manual_intervention_required",
        "plan": plan_entry.get("plan") if plan_entry else None,
        "reason": "rejected",
    }

    return {
        "id": id,
        "status": "manual_intervention_required",
        "message": "Plan rejected. Incident flagged for manual investigation.",
    }
