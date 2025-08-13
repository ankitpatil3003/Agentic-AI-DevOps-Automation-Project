# app/agents/writer_agent.py

from __future__ import annotations
from typing import Dict


class WriterAgent:
    """
    Converts agent outputs into human-readable artifacts (emails, SOPs, summaries).
    Deterministic output for tests; easy to swap with an LLM later.
    """

    @staticmethod
    def management_email(diagnosis: Dict, script: Dict) -> str:
        root = diagnosis.get("root_cause", "unknown")
        evidence = diagnosis.get("evidence") or []
        lint = script.get("lint_passed")
        language = script.get("language", "powershell")

        lines = [
            "Subject: CPU spike incident - analysis & remediation",
            "",
            "Hello Team,",
            "",
            "We investigated the high CPU alerts reported on the Windows Server VM.",
            f"Root cause (preliminary): {root}.",
        ]

        if evidence:
            lines.append("")
            lines.append("Key evidence:")
            lines.extend([f"- {e}" for e in evidence])

        lines += [
            "",
            "Remediation script:",
            f"- Language: {language}",
            f"- Syntax check (lint): {'pass' if lint else 'fail/skip'}",
            "",
            "Action items:",
            "- Continue monitoring perf counters for the next 24 hours.",
            "- Apply latest cumulative updates during the next maintenance window.",
            "",
            "Regards,",
            "Ops Automation",
        ]
        return "\n".join(lines)
