"""Tests for auto-regeneration evaluation metrics + protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

AR_PROTOCOLS = ("autoregeneration_diagnostics", "state_hygiene",
                "checkpoint_repair", "symbol_hygiene", "world_model_hygiene",
                "habit_hygiene", "drift_recovery", "autoregeneration_safety")


def test_metrics_absent():
    assert M.autoregeneration_metrics(None) == {"present": False}


def test_metrics_computed():
    snap = {
        "diagnostics": {"last_state": {"signal_count": 4, "critical_count": 1,
                                       "counts_by_type": {"memory_bloat": 1}}},
        "repair_memory": {"applied_count": 3, "refused_count": 1,
                          "rollback_count": 1, "success_rate": 0.66,
                          "harm_rate": 0.0},
        "proposed_repairs": [{}, {}, {}],
        "state_hygiene": {"quarantined_count": 2},
        "graph_hygiene": {"hypothesis_requests": ["e1"]},
        "habit_hygiene": {"stabilization_requests": []},
        "checkpoint_repair": {"suspect_checkpoints": []},
        "drift_recovery": {"recent_classes": ["runaway", "healthy_adaptation"]},
        "policy": {"mode": "safe_auto_repair"},
    }
    out = M.autoregeneration_metrics(snap)
    assert out["present"] is True
    assert out["degradation_signal_count"] == 4
    assert out["critical_degradation_count"] == 1
    assert out["applied_repair_count"] == 3
    assert out["quarantine_count"] == 2
    assert out["checkpoint_consistency_score"] == 1.0
    assert out["authority"] is False


def test_eight_protocols_registered():
    for name in AR_PROTOCOLS:
        assert name in PROTOCOLS


def test_registry_describes_protocols():
    reg = ExperimentRegistry()
    for name in AR_PROTOCOLS:
        assert name in reg.list_experiments()
        manifest = reg.build_manifest(name, {"steps": 40})
        assert manifest.description
        assert manifest.enabled_features.get("autoregeneration") is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in AR_PROTOCOLS:
        manifest = reg.build_manifest(
            name, {"steps": 40, "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
