"""Integration health: the assembled runtime reports correct wiring."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    HealthStatus,
    IntegrationHealthMonitor,
    RunContext,
    RunMode,
    ScenarioProfileRegistry,
)


def _orch(tmp_path, modules):
    ctx = RunContext(mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path),
                     max_steps=20, enabled_modules=modules)
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(ctx)
    orch.initialize()
    for _ in range(10):
        orch.step()
    return orch


def test_worst_aggregation():
    assert HealthStatus.worst(
        [HealthStatus.HEALTHY, HealthStatus.FAILED]) == HealthStatus.FAILED
    assert HealthStatus.worst([]) == HealthStatus.UNKNOWN


def test_full_profile_is_healthy(tmp_path):
    profile = ScenarioProfileRegistry().require("full_developmental_short")
    profile.run_context.state_dir = str(tmp_path)
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    for _ in range(15):
        orch.step()
    report = IntegrationHealthMonitor().check(orch)
    assert report.healthy
    assert report.overall in (HealthStatus.HEALTHY, HealthStatus.PARTIAL)


def test_report_has_named_checks(tmp_path):
    orch = _orch(tmp_path, ["bridge", "ecology", "governance", "ops"])
    report = IntegrationHealthMonitor().check(orch)
    names = {c.name for c in report.checks}
    assert {"spine", "bus", "registry", "lifecycle", "scheduler",
            "safety"} <= names


def test_unknown_module_is_ignored_not_faked(tmp_path):
    # An unknown module name is silently ignored (never faked, never a crash);
    # the runtime still reports healthy integration.
    orch = _orch(tmp_path, ["bridge", "ecology", "governance",
                            "does_not_exist"])
    report = IntegrationHealthMonitor().check(orch)
    assert report.healthy
    assert "does_not_exist" not in orch.registry.modules
    assert orch.step_count > 0


def test_monitor_keeps_history(tmp_path):
    orch = _orch(tmp_path, ["bridge", "ecology", "governance"])
    mon = IntegrationHealthMonitor()
    mon.check(orch)
    mon.check(orch)
    assert mon.snapshot()["check_count"] == 2
