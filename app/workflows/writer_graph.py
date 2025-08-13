# app/workflows/writer_graph.py

from app.agents.writer_agent import WriterAgent


class WriterGraph:
    """
    Wraps WriterAgent for structured summary generation.
    Can later be extended for multiple output formats (email, PDF, SOP).
    """

    async def run(self, context: dict) -> dict:
        agent_outputs = {
            "diagnosis": context.get("diagnosis"),
            "script": context.get("script")
        }
        summary = WriterAgent.run(agent_outputs)
        context["email_draft"] = summary
        return context
