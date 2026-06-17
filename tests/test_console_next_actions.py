"""Console next actions: generated, blocker forces fix/stop, never executed."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    build_console,
    stage_forbidden_governance,
)
from solaris_ai_nn.tester_console import NextActionPriority  # noqa: E402


def test_next_action_generated(tmp_path):
    rt = build_console(tmp_path)
    assert rt.next_actions
    assert rt.next_actions[0].action


def test_no_fixture_recommends_fixture(tmp_path):
    rt = build_console(tmp_path)
    assert "fixture" in rt.next_actions[0].action.lower()


def test_blocker_forces_fix_or_stop(tmp_path):
    stage_forbidden_governance(os.path.join(str(tmp_path), "live"))
    rt = build_console(tmp_path)
    top = rt.next_actions[0]
    assert top.priority == NextActionPriority.STOP
    assert "fix" in top.action.lower() or "stop" in top.action.lower()


def test_actions_not_executed(tmp_path):
    rt = build_console(tmp_path)
    for a in rt.next_actions:
        assert a.to_dict()["executed_by_console"] is False
