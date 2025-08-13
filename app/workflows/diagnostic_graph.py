# app/workflows/diagnostic_graph.py

from app.agents.diagnostic_agent import DiagnosticAgent


class DiagnosticGraph:
    """
    A simple wrapper class that runs the DiagnosticAgent.
    Can be extended into a LangGraph later if needed.
    """

    async def run(self, context: dict) -> dict:
        request_text = context.get("request", "")
        result = DiagnosticAgent.run(request_text)
        context["diagnosis"] = result
        return context
