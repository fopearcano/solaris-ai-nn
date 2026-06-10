"""Tests for the ExperimentRegistry."""

from __future__ import annotations

import pytest

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry

REQUIRED = ["absence_stimulus", "feedback_inversion", "reward_danger",
            "restart_recovery", "replay_determinism", "substrate_comparison",
            "plasticity_dry_run", "synthesis_pruning", "language_trace"]


def test_required_experiments_registered():
    registry = ExperimentRegistry()
    names = registry.list_experiments()
    for name in REQUIRED:
        assert name in names


def test_unknown_experiment_rejected():
    registry = ExperimentRegistry()
    with pytest.raises(ValueError):
        registry.get("become_conscious")
    with pytest.raises(ValueError):
        registry.build_manifest("nope")


def test_default_config_is_safe():
    registry = ExperimentRegistry()
    cfg = registry.default_config("absence_stimulus")
    assert cfg["steps"] <= 1000
    assert cfg["continuous"] is False


def test_validate_config_rejects_unsafe():
    registry = ExperimentRegistry()
    with pytest.raises(ValueError):
        registry.validate_config("absence_stimulus", {"steps": 0})
    with pytest.raises(ValueError):
        registry.validate_config("absence_stimulus", {"steps": 10_000_000})
    with pytest.raises(ValueError):
        registry.validate_config("absence_stimulus", {"continuous": True})
    with pytest.raises(ValueError):
        registry.validate_config("absence_stimulus", {"substrate": "gpt"})


def test_build_manifest_features():
    registry = ExperimentRegistry()
    m = registry.build_manifest("reward_danger", {"steps": 50})
    assert m.enabled_features["embodiment"] is True
    m2 = registry.build_manifest("language_trace", {"steps": 50})
    assert m2.enabled_features["language"] is True
    assert m2.max_steps == 50 and m2.safety_mode == "bounded"
