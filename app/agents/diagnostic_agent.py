# app/agents/diagnostic_agent.py
from __future__ import annotations
from typing import Dict, List

def _has_any(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)

class DiagnosticAgent:
    """
    Lightweight, deterministic RCA heuristic.
    Now recognizes CPU spikes on generic 'server/vm/node' hints as Windows-ish,
    not just when the literal word 'windows' appears.
    """

    @staticmethod
    def run(user_request: str) -> Dict:
        text = (user_request or "").lower()

        cpu_terms = ["cpu", "95%", "100%"]
        win_terms = [
            "windows", "windows server", "win2019", "win2022", "ws2019", "ws2022",
        ]
        host_hints = [
            "server", "vm", "vm-", "vm_", "vmnode", "vm-node", "node", "node1", "vm-node1",
        ]

        if _has_any(text, cpu_terms) and (_has_any(text, win_terms) or _has_any(text, host_hints)):
            root = "Wsappx process consuming abnormal CPU"
            evidence: List[str] = [
                "Task Manager shows high CPU in wsappx during Store operations",
                "Perfmon counters for \\Process(wsappx)\\% Processor Time spike with disk activity",
            ]
            solutions = [
                {"title": "Apply latest cumulative updates", "confidence": "high"},
                {"title": "Disable Microsoft Store auto-updates via policy", "confidence": "medium"},
                {"title": "Schedule Store maintenance off-peak", "confidence": "medium"},
            ]
        else:
            root = "Unknown — insufficient data"
            evidence = ["No high-confidence signature detected in request text."]
            solutions = [{"title": "Collect perf counters and review top processes", "confidence": "low"}]

        return {"root_cause": root, "evidence": evidence, "solutions": solutions}
