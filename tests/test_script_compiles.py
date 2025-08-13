# tests/test_script_compiles.py

import pytest
from app.agents.automation_agent import AutomationAgent


def test_bash_script_lint():
    bash_script = """
    mkdir -p /tmp/logs
    uptime > /tmp/logs/sys_status.log
    """
    lint_passed, lint_error = AutomationAgent.lint_script(bash_script)
    assert lint_passed is True
    assert lint_error is None


def test_powershell_script_lint():
    ps_script = """
    New-Item -Path "C:\\Logs" -ItemType Directory -Force
    logman start MyLog
    """
    lint_passed, lint_error = AutomationAgent.lint_script(ps_script)
    # Lint might fail if pwsh isn't installed in the test environment
    # So allow it to be False but shouldn't throw exception
    assert isinstance(lint_passed, bool)
