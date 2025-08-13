# app/agents/incident_report_agent.py

from app.integrations.servicenow_client import ServiceNowClient

class IncidentReportAgent:
    @staticmethod
    def create_incident(request_text: str) -> str:
        description = f"[AUTOMATION REQUEST] {request_text}"
        res = ServiceNowClient.create_incident(
            short_description="AI Automation Request",
            description=description,
            caller_username="integration.incidentuser",
        )
        return res["sys_id"]

    @staticmethod
    def post_note(incident_sys_id: str, text: str):
        ServiceNowClient.update_incident(incident_sys_id, work_notes=text)

    @staticmethod
    def resolve_incident(incident_sys_id: str, result: dict):
        """
        Compose final note and transition to Resolved (6).
        SAFELY reads nested keys (no KeyError if diagnose step didn't run).
        """
        notes: list[str] = []

        diag = (result or {}).get("diagnosis") or {}
        rc = diag.get("root_cause")
        if rc:
            notes.append(f"Root Cause: {rc}")
        ev = diag.get("evidence") or []
        if ev:
            notes.append("Evidence:\n- " + "\n- ".join(ev))

        script = (result or {}).get("script") or {}
        lang = script.get("language", "unknown")
        lint = script.get("lint_passed")
        notes.append(f"Script generated in {lang}; Lint passed: {lint}")

        email_draft = (result or {}).get("email_draft") or ""
        if email_draft:
            notes.append("Summary Draft:\n" + email_draft)

        final_notes = "\n".join(notes) or "Automation completed."

        # One PATCH by sys_id with state=6 + resolution fields (Table API best practice)
        ServiceNowClient.update_incident(
            incident_sys_id,
            work_notes=final_notes,
            state=6,
            close_code="Resolved by caller",  # or use your DEFAULT_RESOLUTION_CODE env
            close_notes="Automated remediation applied. See work notes.",
        )

    @staticmethod
    def mark_manual_intervention(incident_sys_id: str):
        ServiceNowClient.update_incident(
            incident_sys_id,
            work_notes="Automation was rejected. Flagged for manual investigation.",
            state=1,
        )
