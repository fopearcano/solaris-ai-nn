"""Evaluation integration: conscience metrics, protocols, registry."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "conscience_minimal_smoke", "conscience_full_short", "scenario_profile",
    "integration_health", "scheduler_cadence", "bus_replay",
    "month_scale_plan",
)


def test_seven_conscience_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_conscience_metrics_absent():
    assert M.conscience_metrics(None) == {"present": False}


def test_conscience_metrics_shape():
    sample = {
        "step_count": 100, "bus_message_count": 200,
        "scheduler_skip_count": 50, "enabled_modules": ["a", "b"],
        "missing_modules": [], "degraded_modules": [],
        "snapshot": {"spine": {"status_counts": {"ran": 90, "degraded": 0}},
                     "safety": {"rejected_count": 0}},
    }
    out = M.conscience_metrics(sample, scenario={"ok": True,
                                                 "runtime_seconds": 1.2})
    keys = {"run_step_count", "spine_phase_count", "bus_message_count",
            "module_success_rate", "module_failure_rate",
            "degraded_module_count", "scheduler_skip_count",
            "checkpoint_success_rate", "scenario_exit_success",
            "profile_runtime_seconds", "report_generation_success",
            "safety_violation_count", "governance_block_count"}
    assert keys <= set(out)
    assert out["module_success_rate"] == 1.0
    assert out["scenario_exit_success"] is True


def test_failure_rate_when_phases_degraded():
    sample = {"snapshot": {"spine": {"status_counts": {"ran": 5,
                                                       "degraded": 5}}}}
    out = M.conscience_metrics(sample)
    assert out["module_failure_rate"] == 0.5


def test_registry_builds_conscience_manifest():
    reg = ExperimentRegistry()
    assert "conscience_minimal_smoke" in reg.list_experiments()
    manifest = reg.build_manifest("conscience_minimal_smoke", {"steps": 12})
    assert manifest.enabled_features.get("conscience_orchestrator") is True


def test_minimal_smoke_protocol_runs(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest(
        "conscience_minimal_smoke",
        {"steps": 12, "state_dir": str(tmp_path)})
    result = PROTOCOLS["conscience_minimal_smoke"](manifest)
    assert result.success
    assert result.metrics["conscience"]["run_step_count"] == 12
