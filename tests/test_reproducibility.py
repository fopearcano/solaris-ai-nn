"""Tests for reproducibility hashing and run comparison."""

from __future__ import annotations

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest, ExperimentResult
from solaris_ai_nn.evaluation.reproducibility import (
    check_seed_stability,
    compare_runs,
    compute_reproducibility_hash,
)
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def _manifest(seed=7):
    return ExperimentManifest(name="x", seed=seed, substrate="esn",
                              max_steps=50)


def test_hash_is_stable_and_sensitive():
    a = compute_reproducibility_hash(_manifest(), {"k": 1})
    b = compute_reproducibility_hash(_manifest(), {"k": 1})
    assert a == b  # stable across calls (id/timestamp excluded)
    c = compute_reproducibility_hash(_manifest(seed=8), {"k": 1})
    assert a != c  # seed changes the hash


def test_same_seed_comparison_matches():
    metrics = {"continuity": {"heartbeat_count": 10},
               "reactivity": {"stimulus_count": 10, "reaction_count": 5,
                              "executed_action_count": 3},
               "adaptation": {"prediction_error_end": 0.5},
               "substrate": {"state_norm": 4.2}}
    a = ExperimentResult(manifest=_manifest(), metrics=dict(metrics))
    b = ExperimentResult(manifest=_manifest(), metrics=dict(metrics))
    report = compare_runs(a, b)
    assert report.same_seed and report.match
    assert not report.warnings


def test_mismatch_produces_warning():
    a = ExperimentResult(manifest=_manifest(),
                         metrics={"substrate": {"state_norm": 4.0}})
    b = ExperimentResult(manifest=_manifest(),
                         metrics={"substrate": {"state_norm": 5.0}})
    report = compare_runs(a, b)
    assert report.match is False
    assert any("nondeterminism" in w for w in report.warnings)


def test_different_seed_flagged():
    a = ExperimentResult(manifest=_manifest(7), metrics={})
    b = ExperimentResult(manifest=_manifest(8), metrics={})
    report = compare_runs(a, b)
    assert report.same_seed is False
    assert any("different seeds" in w for w in report.warnings)


def test_seed_stability_end_to_end(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path / "bench"))
    report = check_seed_stability("synthesis_pruning", seed=7, repeats=2,
                                  steps=30, runner=runner)
    assert report.same_seed is True
    assert report.match is True
