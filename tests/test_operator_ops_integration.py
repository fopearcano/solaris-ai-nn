"""Operator <-> Ops: status includes console paths; prohibited run warns."""

from __future__ import annotations

from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


class _Runner:
    def __init__(self, console):
        self.operator_console = console


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_console_paths(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "available_profile_count": 60,
        "blocked_profile_count": 3,
        "latest_status_board_path": "/x/STATUS_BOARD.md",
        "latest_decision_board_path": "/x/DECISION_BOARD.md",
        "latest_session_log_path": "/x/session_log.jsonl"})
    status = sup.operator_console_status()
    assert status["operator_console_enabled"] is True
    assert status["latest_status_board_path"] == "/x/STATUS_BOARD.md"
    assert status["latest_decision_board_path"] == "/x/DECISION_BOARD.md"
    assert status["real_world_authority"] is False


def test_ops_records_prohibited_run_warning(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "attempted_prohibited_run": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "operator_prohibited_run" in types


def test_ops_records_forbidden_approval_warning(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "attempted_forbidden_approval": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "operator_forbidden_approval" in types
