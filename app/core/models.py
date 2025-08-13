# app/core/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict


# ===== EXECUTE API SCHEMA =====

class ExecuteRequest(BaseModel):
    request: str = Field(..., description="Natural-language request")
    require_approval: bool = Field(False, description="If true, pause for approval before automation")


class ScriptResult(BaseModel):
    language: Literal["bash", "powershell"]
    code: str
    lint_passed: bool
    lint_error: Optional[str] = None


class DiagnosisSolution(BaseModel):
    title: str
    confidence: Literal["low", "medium", "high"]


class DiagnosisResult(BaseModel):
    root_cause: str
    evidence: List[str]
    solutions: List[DiagnosisSolution]


class ExecuteResponse(BaseModel):
    incident_sys_id: str
    status: Literal["awaiting_approval", "resolved", "manual_intervention_required"]
    message: Optional[str] = None
    diagnosis: Optional[DiagnosisResult] = None
    script: Optional[ScriptResult] = None
    email_draft: Optional[str] = None
    servicenow_updated: Optional[bool] = None


# ===== PLAN STATUS / TASK TRACKING =====

class TaskStatus(str):
    ACTIVE = "active"
    WAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "resolved"
    FAILED = "manual_intervention_required"
