"""Tests for the long-horizon metrics."""

from __future__ import annotations

from solaris_ai_nn.developmental.long_horizon_metrics import (
    FORBIDDEN_METRIC_NAMES,
    long_horizon_metrics,
)

MOCK_STATE = {
    "clock": {"cumulative_lifetime_s": 720 * 3600,
              "active_runtime_ratio": 0.95, "restart_gap_count": 3,
              "total_memory_consolidations": 12},
    "memory": {"fossil_count": 8, "compression_ratio": 0.2},
    "growth": {"structural_change_score": 0.3,
               "stagnation_windows": 1},
    "drift": {"drift_velocity": 0.05},
    "milestones": {"count": 10},
    "epochs": {"transition_count": 4},
    "identity_continuity": 0.95,
    "boundary_violation_count": 1,
    "world_model_node_count": 400,
    "pruning_count": 6,
    "prediction_accuracy_trend": 0.1,
    "phase_transition_candidates": 2,
}


def test_metrics_computed_from_mock_data():
    metrics = long_horizon_metrics(MOCK_STATE)
    assert metrics["present"] is True
    assert metrics["lifetime_runtime_hours"] == 720.0
    assert metrics["restart_recovery_count"] == 3
    assert metrics["consolidation_count"] == 12
    assert metrics["fossil_memory_count"] == 8
    assert metrics["compression_ratio"] == 0.2
    assert metrics["drift_velocity"] == 0.05
    assert metrics["stagnation_duration"] == 1
    assert metrics["epoch_transition_count"] == 4
    assert metrics["phase_transition_candidate_count"] == 2
    assert metrics["milestone_rate"] > 0
    assert 0 <= metrics["boundary_stability_score"] <= 1
    assert long_horizon_metrics(None) == {"present": False}


def test_no_consciousness_or_life_score_exists():
    metrics = long_horizon_metrics(MOCK_STATE)
    for forbidden in FORBIDDEN_METRIC_NAMES:
        assert forbidden not in metrics, forbidden
    # And the forbidden names appear in the source only inside the
    # FORBIDDEN_METRIC_NAMES guard tuple itself.
    import importlib

    module = importlib.import_module(
        "solaris_ai_nn.developmental.long_horizon_metrics")
    source = open(module.__file__, encoding="utf-8").read()
    assert source.count("consciousness_score") == 1
    assert source.count('"life_score"') == 1


def test_cautious_scores_exist():
    metrics = long_horizon_metrics(MOCK_STATE)
    assert "structural_change_score" in metrics
    assert "developmental_stability_score" in metrics
    assert "long_horizon_adaptation_proxy" in metrics
    assert 0 <= metrics["developmental_stability_score"] <= 1
    assert "how little they prove" in metrics["note"]
