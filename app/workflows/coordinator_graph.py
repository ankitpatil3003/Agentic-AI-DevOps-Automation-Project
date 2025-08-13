# app/workflows/coordinator_graph.py

from app.agents.coordinator_agent import CoordinatorAgent

def run_agentic_flow(incident_sys_id: str, user_request: str) -> dict:
    """
    Delegates to CoordinatorAgent, which:
      1) builds a plan from the free-form request
      2) runs only the needed agents (diagnose/script/email)
      3) posts incremental notes and resolves the incident
    """
    return CoordinatorAgent.run(incident_sys_id, user_request)
