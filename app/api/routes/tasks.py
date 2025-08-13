# app/api/routes/tasks.py

from fastapi import APIRouter, HTTPException
from requests import HTTPError
import requests

from app.integrations.servicenow_client import ServiceNowClient
from app.core.task_store import task_store

router = APIRouter(prefix="/api/v1", tags=["v1"])

# map numeric incident_state to human-ish label (SN core states)
_STATE_LABEL = {
    "1": "New",
    "2": "In Progress",
    "3": "On Hold",
    "6": "Resolved",
    "7": "Closed",
    "8": "Canceled",
}
_COMPL_STATES = {"6", "7"}  # Resolved/Closed


def _derive_status_from_incident(state: str, updates: list[str]) -> str:
    """
    Translate ServiceNow state + notes into API-level status when no store state exists.
    - completed: when state in Resolved/Closed
    - waiting_approval: when still New and no automation notes posted yet
    - active: otherwise
    """
    s = str(state or "")
    if s in _COMPL_STATES:
        return "completed"
    notes_blob = "\n".join(updates).lower()
    if s == "1" and not any(k in notes_blob for k in ("plan started", "approval received", "executing agentic plan")):
        return "waiting_approval"
    return "active"


def _fetch_journal_entries(incident_sys_id: str) -> list[dict]:
    """
    Fetch work notes + comments from sys_journal_field for this incident.
    Requires read ACLs to that table; if not available, returns [].
    """
    base = ServiceNowClient.INSTANCE_URL
    url = f"{base}/api/now/table/sys_journal_field"

    # Only notes for this record; order oldest->newest
    query = f"name=incident^elementINcomments,work_notes^documentkey={incident_sys_id}^ORDERBYsys_created_on"
    params = {
        "sysparm_query": query,
        "sysparm_fields": "sys_created_on,sys_created_by,element,value",
        "sysparm_display_value": "true",
        "sysparm_limit": "100",
    }

    try:
        r = requests.get(
            url,
            headers=ServiceNowClient.HEADERS,
            auth=ServiceNowClient._get_auth(),
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        rows = r.json().get("result", [])
        return [
            {
                "timestamp": row.get("sys_created_on"),
                "author": row.get("sys_created_by"),
                "type": row.get("element"),  # "work_notes" or "comments"
                "text": row.get("value", "") or "",
            }
            for row in rows
        ]
    except Exception:
        # If ACLs block access, degrade gracefully
        return []


@router.get("/tasks/{id}")
async def get_task(id: str):
    """
    Return current task/incident status and a simple timeline of updates.
    Approval workflow status prefers task_store; otherwise derive from SN.
    """
    # Load any stored approval/workflow status
    store = task_store.get(id) or {}
    store_status = store.get("status")

    try:
        inc = ServiceNowClient.get_incident(id)   # READ by sys_id
    except HTTPError as e:
        raise HTTPException(status_code=404, detail=f"Incident not found or not accessible: {e}") from e

    state = str(inc.get("state") or inc.get("incident_state") or "")
    state_label = _STATE_LABEL.get(state, f"State {state or 'unknown'}")

    # Timeline from journal (work notes + comments)
    journal = _fetch_journal_entries(id)
    updates_texts = [j.get("text", "") for j in journal if j.get("text")]

    # Precedence rules:
    # 1) If SN says completed (Resolved/Closed), it's completed.
    # 2) If store says manual_intervention_required (or rejected), honor that.
    # 3) If store says waiting_approval/awaiting_approval, reflect that.
    # 4) Otherwise derive from SN state + notes.
    if state in _COMPL_STATES:
        status = "completed"
    elif store_status in ("manual_intervention_required", "rejected"):
        status = "manual_intervention_required"
    elif store_status in ("waiting_approval", "awaiting_approval"):
        status = "waiting_approval"
    else:
        status = _derive_status_from_incident(state, updates_texts)

    return {
        "incident_sys_id": id,
        "number": inc.get("number"),
        "short_description": inc.get("short_description"),
        "state": state,
        "state_label": state_label,
        "status": status,                # active | waiting_approval | completed | manual_intervention_required
        "updates": journal,              # [{timestamp,author,type,text}, ...]
        "plan": store.get("plan"),
        "result": store.get("result"),
    }
