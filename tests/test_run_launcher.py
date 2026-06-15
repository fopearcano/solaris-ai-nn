"""RunLauncher: unknown/prohibited blocked; confirm required; safety blocks."""

from __future__ import annotations

from solaris_ai_nn.operator_console import (
    OperatorConsoleConfig,
    ProfileCatalog,
    RunLauncher,
)


class _FakeResult:
    ok = True
    run_id = "RID_1"
    status = "completed"
    report_path = "/tmp/report.json"


class _FakeRunner:
    def __init__(self):
        self.calls = []

    def run_profile(self, profile_id, governance_approved=False):
        self.calls.append(profile_id)
        return _FakeResult()


def _launcher(tmp_path, runner=None):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    return RunLauncher(cfg, ProfileCatalog(), runner=runner)


def test_unknown_profile_blocked(tmp_path):
    result = _launcher(tmp_path).launch("nope", operator_confirmed=True)
    assert result.blocked
    assert result.blockers[0].reason == "unknown_profile"


def test_prohibited_profile_blocked(tmp_path):
    result = _launcher(tmp_path).launch("pilot1_30d_soak",
                                        operator_confirmed=True,
                                        safety_state={"status": "ok"})
    assert result.blocked
    assert result.blockers[0].reason in (
        "not_runnable_from_console", "unbounded_long_run")


def test_bounded_profile_requires_confirm(tmp_path):
    result = _launcher(tmp_path).launch("safety_fast_check",
                                        operator_confirmed=False)
    assert result.blocked
    assert result.blockers[0].reason == "operator_confirmation_required"


def test_critical_safety_failure_blocks_run(tmp_path):
    result = _launcher(tmp_path).launch(
        "safety_fast_check", operator_confirmed=True,
        safety_state={"critical_failure": True})
    assert result.blocked
    assert result.blockers[0].reason == "critical_safety_failure"


def test_missing_safety_state_blocks_run(tmp_path):
    result = _launcher(tmp_path).launch("safety_fast_check",
                                        operator_confirmed=True,
                                        safety_state=None)
    assert result.blocked
    assert result.blockers[0].reason == "missing_safety_state"


def test_orchestrator_unavailable_blocks(tmp_path):
    # All gates pass, but no ScenarioRunner is attached: the launcher runs
    # nothing on its own.
    result = _launcher(tmp_path).launch("minimal_smoke", operator_confirmed=True,
                                        safety_state={"status": "ok"})
    assert result.blocked
    assert result.blockers[0].reason == "orchestrator_unavailable"


def test_allowed_run_uses_orchestrator(tmp_path):
    runner = _FakeRunner()
    result = _launcher(tmp_path, runner=runner).launch(
        "minimal_smoke", operator_confirmed=True,
        safety_state={"status": "ok"})
    assert result.launched
    assert runner.calls == ["minimal_smoke"]
