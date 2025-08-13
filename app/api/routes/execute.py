# app/api/routes/execute.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.incident_report_agent import IncidentReportAgent
from app.workflows.coordinator_graph import run_agentic_flow

router = APIRouter(prefix="/api/v1", tags=["v1"])


class ExecuteRequest(BaseModel):
    request: str
    require_approval: bool = False


@router.post("/execute")
async def execute(req: ExecuteRequest):
    """
    Auto-execute path:
      - create incident with mandatory fields
      - run agents with incremental updates
      - resolve with resolution fields
    Approval path:
      - create incident and return waiting_approval (no automation yet)
    """
    try:
        # 1) create & capture authoritative sys_id
        incident_sys_id = IncidentReportAgent.create_incident(req.request)

        # 2) approval or auto-run
        if req.require_approval:
            # in your approve/reject routes, call IncidentReportAgent.* using this sys_id
            plan = {
                "steps": ["Run diagnostics", "Generate remediation script", "Draft summary", "Resolve incident"],
                "summary": "Agentic plan prepared. Awaiting approval to execute.",
            }
            return {
                "incident_sys_id": incident_sys_id,
                "status": "waiting_approval",
                "plan": plan,
                "message": "The incident has been reported. Awaiting approval before initiating automation.",
            }

        # 3) auto execute in-process (first test case)
        result = run_agentic_flow(incident_sys_id, req.request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
