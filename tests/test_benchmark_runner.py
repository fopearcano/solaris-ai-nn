"""Tests for the BenchmarkRunner."""

from __future__ import annotations

import json
from pathlib import Path

from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_single_experiment_runs_and_writes_files(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path / "bench"))
    result = runner.run_experiment("synthesis_pruning", {"steps": 30})
    assert result.success
    run_dir = tmp_path / "bench" / "runs" / result.manifest.experiment_id
    for name in ("manifest.json", "result.json", "result.md", "artifacts.json"):
        assert (run_dir / name).exists(), name
    data = json.loads((run_dir / "result.json").read_text())
    assert data["manifest"]["name"] == "synthesis_pruning"
    assert "scores" in data["metrics"]


def test_suite_runs_and_summarizes(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path / "bench"))
    results = runner.run_suite(["synthesis_pruning", "absence_stimulus"],
                               {"steps": 40})
    assert len(results) == 2
    assert all(r.success for r in results)
    assert (tmp_path / "bench" / "suite_summary.json").exists()
    assert (tmp_path / "bench" / "suite_summary.md").exists()
    summary = runner.summarize(results)
    assert len(summary["experiments"]) == 2


def test_unknown_experiment_in_suite_is_skipped(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path / "bench"))
    results = runner.run_suite(["synthesis_pruning", "not_a_thing"],
                               {"steps": 30})
    assert len(results) == 1  # bad name skipped, suite continues


def test_failure_captured_gracefully(tmp_path):
    from solaris_ai_nn.evaluation.benchmark import ExperimentManifest, ExperimentResult

    runner = BenchmarkRunner(output_dir=str(tmp_path / "bench"))

    def exploding_protocol(manifest):
        from solaris_ai_nn.evaluation.protocols import _run

        def body(m):
            raise RuntimeError("intentional test failure")
        return _run(manifest, body)

    runner.registry.register("exploder", exploding_protocol)
    result = runner.run_experiment("exploder", {"steps": 10})
    assert result.success is False
    assert "intentional test failure" in result.error
    assert any(f["name"] == "experiment_error"
               for f in result.metrics["failure_findings"])
