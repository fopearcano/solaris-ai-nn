"""Operator <-> Conscience: allowed runs use the ScenarioRunner path only."""

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
    report_path = "/tmp/r.json"


class _RecordingRunner:
    """Stands in for the conscience ScenarioRunner; records calls."""

    def __init__(self):
        self.calls = []

    def run_profile(self, profile_id, governance_approved=False):
        self.calls.append((profile_id, governance_approved))
        return _FakeResult()


def test_allowed_run_uses_scenario_runner(tmp_path):
    runner = _RecordingRunner()
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    launcher = RunLauncher(cfg, ProfileCatalog(), runner=runner)
    result = launcher.launch("minimal_smoke", operator_confirmed=True,
                             safety_state={"status": "ok"})
    assert result.launched
    # The run went through the orchestrator's run_profile, not any direct call.
    assert runner.calls == [("minimal_smoke", False)]


def test_no_direct_module_bypass(tmp_path):
    # Without a ScenarioRunner attached, the launcher runs nothing on its own:
    # there is no alternate path into the motor/sensory layers.
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    launcher = RunLauncher(cfg, ProfileCatalog(), runner=None)
    result = launcher.launch("minimal_smoke", operator_confirmed=True,
                             safety_state={"status": "ok"})
    assert result.blocked
    assert result.blockers[0].reason == "orchestrator_unavailable"


def test_launcher_has_no_shell_or_network():
    import inspect

    from solaris_ai_nn.operator_console import run_launcher

    src = inspect.getsource(run_launcher)
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "import socket" not in src
