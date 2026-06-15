"""Operator <-> Safety invariants: missing state blocks; critical failure blocks."""

from __future__ import annotations

from solaris_ai_nn.operator_console import (
    OperatorConsoleConfig,
    ProfileCatalog,
    RunLauncher,
)


class _FakeResult:
    ok = True
    run_id = "RID"
    status = "completed"
    report_path = None


class _FakeRunner:
    def run_profile(self, profile_id, governance_approved=False):
        return _FakeResult()


def _launcher(tmp_path, runner=None):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    return RunLauncher(cfg, ProfileCatalog(), runner=runner)


def test_missing_safety_state_blocks_or_recommends(tmp_path):
    result = _launcher(tmp_path, runner=_FakeRunner()).launch(
        "safety_fast_check", operator_confirmed=True, safety_state=None)
    assert result.blocked
    blocker = result.blockers[0]
    assert blocker.reason == "missing_safety_state"
    assert "fast safety check" in blocker.recommendation.lower()


def test_critical_safety_failure_blocks_run(tmp_path):
    result = _launcher(tmp_path, runner=_FakeRunner()).launch(
        "safety_fast_check", operator_confirmed=True,
        safety_state={"unresolved_blocker_count": 1})
    assert result.blocked
    assert result.blockers[0].reason == "critical_safety_failure"


def test_safe_state_allows_run(tmp_path):
    result = _launcher(tmp_path, runner=_FakeRunner()).launch(
        "minimal_smoke", operator_confirmed=True,
        safety_state={"status": "ok", "unresolved_blocker_count": 0})
    assert result.launched
