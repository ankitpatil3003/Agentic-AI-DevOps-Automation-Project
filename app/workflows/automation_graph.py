# app/workflows/automation_graph.py

from app.agents.automation_agent import AutomationAgent


class AutomationGraph:
    """
    Wrapper around AutomationAgent.
    Can be expanded later to support retries, validation, or fallback tooling.
    """

    async def run(self, context: dict) -> dict:
        request_text = context.get("request", "")
        result = AutomationAgent.run(request_text)
        context["script"] = result
        return context
