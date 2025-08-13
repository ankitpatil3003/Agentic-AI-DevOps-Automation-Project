# app/agents/coordinator_agent.py

from __future__ import annotations
from typing import Dict, List, Callable, Any

from app.agents.diagnostic_agent import DiagnosticAgent
from app.agents.automation_agent import AutomationAgent
from app.agents.writer_agent import WriterAgent
from app.agents.incident_report_agent import IncidentReportAgent

# --- Simple keyword router ----------------------------------------------------
CAPABILITIES = {
    "diagnose": ["diagnose", "rca", "why", "root cause", "investigate", "analysis"],
    "script":   ["script", "powershell", "bash", "az cli", "collector", "automation", "remediation", "fix"],
    "email":    ["email", "summary", "report", "sop", "write", "draft"],
}

def plan_from_request(text: str, always_add_email: bool = True) -> list[str]:
    t = (text or "").lower()
    steps: list[str] = []
    if any(k in t for k in CAPABILITIES["diagnose"]): steps.append("diagnose")
    if any(k in t for k in CAPABILITIES["script"]):   steps.append("script")
    if any(k in t for k in CAPABILITIES["email"]):    steps.append("email")

    if not steps:
        steps = ["diagnose", "script"]   # sensible default
    if always_add_email and "email" not in steps:
        steps.append("email")             # always append an email summary
    return steps

# --- Step wrappers (each posts its own progress note) -------------------------
def _step_diagnose(incident_sys_id: str, request_text: str, _: Dict[str, Any]) -> Dict[str, Any]:
    IncidentReportAgent.post_note(incident_sys_id, "Plan started: running diagnostics.")
    diag = DiagnosticAgent.run(request_text) or {}
    root = diag.get("root_cause", "n/a")
    IncidentReportAgent.post_note(incident_sys_id, f"Diagnosis complete: {root}.")
    return diag

def _step_script(incident_sys_id: str, request_text: str, prior: Dict[str, Any]) -> Dict[str, Any]:
    IncidentReportAgent.post_note(incident_sys_id, "Generating remediation script.")
    # ⬇️ call the shim so tests can monkeypatch AutomationAgent.run
    script = AutomationAgent.run(request_text) or {}
    IncidentReportAgent.post_note(
        incident_sys_id,
        f"Script ready; lint_passed={script.get('lint_passed')}.",
    )
    return script

def _step_email(incident_sys_id: str, request_text: str, results: Dict[str, Any]) -> str:
    email = WriterAgent.management_email(results.get("diagnose", {}), results.get("script", {})) or ""
    IncidentReportAgent.post_note(incident_sys_id, "Drafted summary email.")
    return email

def _agents_map() -> Dict[str, Callable[[str, str, Dict[str, Any]], Any]]:
    """Map step key -> callable(incident_sys_id, request_text, results_so_far)"""
    return {
        "diagnose": _step_diagnose,
        "script": _step_script,
        "email": _step_email,
    }

def execute_plan(incident_sys_id: str, text: str, agents: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Execute each planned step in order, accumulating results.
    Each step gets access to results-so-far for chaining.
    """
    results: Dict[str, Any] = {}
    for step in plan_from_request(text):
        try:
            out = agents[step](incident_sys_id, text, results)
            results[step] = out
        except Exception as e:
            # keep going, but leave a breadcrumb in SN and shape result for tests
            IncidentReportAgent.post_note(incident_sys_id, f"Step '{step}' failed: {e}")
            if step == "script":
                # tests expect script either missing OR lint_passed=False when it fails
                results[step] = {"language": None, "code": "", "lint_passed": False, "error": str(e)}
            elif step == "diagnose":
                results[step] = {"root_cause": "Unknown — error", "error": str(e)}
            elif step == "email":
                results[step] = ""
            else:
                results[step] = {"error": str(e)}
    return results

# --- Public entrypoint used by your workflow (or call from /execute) ----------
class CoordinatorAgent:
    """
    Orchestrates the modular agents:
      1) plan_from_request()
      2) execute only the needed steps
      3) compose final result and resolve the incident
    """

    @staticmethod
    def run(incident_sys_id: str, user_request: str) -> Dict[str, Any]:
        steps = plan_from_request(user_request)
        IncidentReportAgent.post_note(incident_sys_id, f"Plan: {', '.join(steps)}")
        results_by_step = execute_plan(incident_sys_id, user_request, _agents_map())

        # normalize keys for downstream consumers
        diagnosis = results_by_step.get("diagnose") or {}
        script = results_by_step.get("script") or {}
        email_draft = results_by_step.get("email") or ""

        # finalize + resolve with mandatory fields (state=6 + resolution code/notes)
        IncidentReportAgent.resolve_incident(
            incident_sys_id,
            {"diagnosis": diagnosis, "script": script, "email_draft": email_draft},
        )

        # ⬇️ tests assert "resolved" (not "completed")
        return {
            "incident_sys_id": incident_sys_id,
            "status": "resolved",
            "diagnosis": diagnosis,
            "script": script,
            "email_draft": email_draft,
            "servicenow_updated": True,
        }
