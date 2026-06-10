"""Tests for benchmark manifest/result schemas."""

from __future__ import annotations

from solaris_ai_nn.evaluation.benchmark import (
    BenchmarkRun,
    BenchmarkSuite,
    ExperimentManifest,
    ExperimentResult,
)


def test_manifest_serializes_with_required_fields():
    m = ExperimentManifest(name="absence_stimulus", seed=3,
                           substrate="liquid_state", max_steps=100,
                           state_dir="/tmp/x")
    d = m.to_dict()
    for key in ("experiment_id", "name", "created_at", "seed", "substrate",
                "substrate_config", "run_config", "enabled_features",
                "max_steps", "max_duration_s", "state_dir",
                "expected_artifacts", "safety_mode"):
        assert key in d
    assert d["safety_mode"] == "bounded"
    back = ExperimentManifest.from_dict(d)
    assert back.experiment_id == m.experiment_id
    assert back.substrate == "liquid_state"


def test_result_serializes():
    m = ExperimentManifest(name="x")
    r = ExperimentResult(manifest=m, success=True, started_at=1.0, ended_at=2.5,
                         metrics={"continuity": {"heartbeat_count": 5}},
                         reproducibility_hash="abc", warnings=["w"])
    d = r.to_dict()
    assert d["success"] is True
    assert d["duration"] == 1.5
    assert d["metrics"]["continuity"]["heartbeat_count"] == 5
    back = ExperimentResult.from_dict(d)
    assert back.manifest.name == "x"
    assert back.reproducibility_hash == "abc"


def test_benchmark_run_and_suite_fields():
    m = ExperimentManifest(name="x")
    r = ExperimentResult(manifest=m, success=True)
    run = BenchmarkRun(manifest=m, result=r, run_dir="/tmp/run")
    assert run.to_dict()["run_dir"] == "/tmp/run"
    suite = BenchmarkSuite()
    suite.add(r)
    suite.add(ExperimentResult(manifest=m, success=False, error="boom"))
    d = suite.to_dict()
    assert d["experiments"] == 2 and d["succeeded"] == 1 and d["failed"] == 1
