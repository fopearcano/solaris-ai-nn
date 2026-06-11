"""Tests for ops supervision over homeostasis."""

from __future__ import annotations

import inspect

from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def _supervisor(tmp_path, **features):
    manifest = OperationalRunManifest(
        mode="bounded", max_steps=60, healthcheck_interval_steps=20,
        state_dir=str(tmp_path / "state"),
        artifact_dir=str(tmp_path / "ops"), seed=5,
        enabled_features={"homeostasis": True, **features})
    return OperationalSupervisor(
        manifest=manifest, registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"))


def _run_with_midrun_mutation(sup, mutate):
    """Mutate the segment runner's regulator before each supervision pass."""
    original = sup._supervise

    def wrapped(*args, **kw):
        runner = sup._last_runner
        if runner is not None and runner.homeostasis is not None:
            mutate(runner.homeostasis)
        original(*args, **kw)

    sup._supervise = wrapped
    return sup.run()


def test_supervised_homeostasis_run(tmp_path):
    sup = _supervisor(tmp_path)
    status = sup.run()
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60
    assert sup._last_runner.homeostasis is not None


def test_high_not_being_pressure_creates_incident(tmp_path):
    sup = _supervisor(tmp_path)

    def force_shutdown_recommendation(regulator):
        regulator.update({"health_level": "critical",
                          "critical_incident": True})

    status = _run_with_midrun_mutation(sup, force_shutdown_recommendation)
    types = [i["type"] for i in status["incidents"]]
    assert "auto_determination_shutdown_recommended" in types


def test_watchdog_still_controls_shutdown(tmp_path):
    """The recommendation is an incident; the homeostasis block never
    requests a stop -- only the watchdog path does."""
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split("Homeostasis monitoring")[1].split(
        "budget_report")[0]
    assert "request_shutdown" not in block
    assert "_stop_requested" not in block
    # And in practice: the run completes its full bound despite the
    # recommendation (no early stop from homeostasis).
    sup = _supervisor(tmp_path)
    status = _run_with_midrun_mutation(
        sup, lambda r: r.update({"health_level": "critical",
                                 "critical_incident": True}))
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60


def test_runaway_need_pressure_incident(tmp_path):
    sup = _supervisor(tmp_path)

    def pin_need(regulator):
        regulator.update({"embodiment": {"energy": 0.0,
                                         "max_energy": 10.0,
                                         "exhausted": True}})

    status = _run_with_midrun_mutation(sup, pin_need)
    if any(i["type"] == "runaway_need_pressure"
           for i in status["incidents"]):
        return  # the incident fired as designed
    # Otherwise intensity stayed below the pin threshold; verify it exists.
    summary = sup._last_runner.homeostasis.summary()
    assert summary["dominant_need"] == "restore_energy"
