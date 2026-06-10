"""Tests for the benchmark protocols (bounded, self-contained)."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.evaluation.benchmark import ExperimentResult
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

REGISTRY = ExperimentRegistry()
FAST = ["absence_stimulus", "synthesis_pruning", "plasticity_dry_run",
        "restart_recovery", "feedback_inversion"]


@pytest.mark.parametrize("name", sorted(PROTOCOLS))
def test_protocol_returns_experiment_result(name, tmp_path):
    start = time.perf_counter()
    manifest = REGISTRY.build_manifest(name, {
        "steps": 40, "state_dir": str(tmp_path / name)})
    result = PROTOCOLS[name](manifest)
    elapsed = time.perf_counter() - start
    assert isinstance(result, ExperimentResult)
    assert elapsed < 90.0  # bounded
    assert result.success, result.error
    assert "scores" in result.metrics
    assert result.reproducibility_hash
    assert result.limitations  # honesty section always present


def test_protocol_failure_is_captured_not_raised(tmp_path):
    manifest = REGISTRY.build_manifest("absence_stimulus", {"steps": 40})
    manifest.run_config["steps"] = "not_a_number"  # poison after validation
    result = PROTOCOLS["absence_stimulus"](manifest)
    assert isinstance(result, ExperimentResult)
    assert result.success is False
    assert "ValueError" in result.error


def test_replay_protocol_reports_determinism(tmp_path):
    manifest = REGISTRY.build_manifest("replay_determinism", {
        "steps": 40, "state_dir": str(tmp_path / "replay")})
    result = PROTOCOLS["replay_determinism"](manifest)
    assert result.metrics["reproducibility"]["deterministic"] is True
