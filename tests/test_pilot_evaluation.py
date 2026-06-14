"""Pilot-1 <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "pilot1_plan", "pilot1_preflight", "pilot1_restart_drill",
    "pilot1_dashboard", "pilot1_daily_review", "pilot1_exit_criteria",
    "pilot1_safety",
)


def test_seven_pilot_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_pilot1_metrics_absent():
    assert M.pilot1_metrics(None) == {"present": False}


def test_pilot1_metrics_shape():
    out = M.pilot1_metrics({
        "elapsed_seconds": 7200.0, "uptime_ratio": 0.99, "restart_count": 1,
        "checkpoint_success": 40, "checkpoint_failure": 0,
        "daily_report_count": 2, "weekly_report_count": 1,
        "incident_count": 1, "failure_mode_count": 0,
        "disk_mb": 100.0, "disk_budget_mb": 2048.0,
        "structural_change_score": 0.2, "stagnation_seconds": 3600.0,
        "exit_success": True, "observability_complete": True,
        "pilot_report_generated": True})
    for key in ("pilot_elapsed_hours", "pilot_uptime_ratio",
                "pilot_restart_count", "checkpoint_success_rate",
                "daily_report_count", "weekly_report_count", "incident_rate",
                "failure_mode_count", "resource_budget_usage_ratio",
                "structural_change_delta_month", "stagnation_hours",
                "pilot_exit_success", "pilot_analyzability_score"):
        assert key in out
    assert out["pilot_elapsed_hours"] == 2.0
    assert out["checkpoint_success_rate"] == 1.0


def test_pilot_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("pilot1_plan", "pilot1_safety", "pilot1_exit_criteria"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success
        assert result.metrics["pilot"]["present"] is True


def test_registry_sets_pilot_feature(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("pilot1_plan", {"steps": 8})
    assert manifest.enabled_features.get("pilot1") is True
