"""Tests for the combined benchmark report generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GENERATE = REPO / "examples" / "generate_benchmark_report.py"

SAMPLE_RESULT = {
    "manifest": {"experiment_id": "abc123", "name": "absence_stimulus",
                 "seed": 7, "substrate": "esn",
                 "enabled_features": {"plasticity": False}},
    "success": True, "started_at": 0.0, "ended_at": 1.0,
    "metrics": {"scores": {"domains": {
        "continuity_score": {"score": 1.0, "explanation": "ok"}}},
        "substrate": {"state_norm": 4.0}},
    "artifacts": {}, "reproducibility_hash": "deadbeef",
    "warnings": [], "limitations": ["heuristic"],
}


def test_combined_report_from_sample_json(tmp_path):
    run_dir = tmp_path / "runs" / "abc123"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text(json.dumps(SAMPLE_RESULT))

    proc = subprocess.run(
        [sys.executable, str(GENERATE), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stderr
    combined = tmp_path / "combined_report.md"
    assert combined.exists()
    md = combined.read_text()
    assert "# Combined benchmark report" in md
    assert "absence_stimulus" in md
    assert "Limitations and Unknowns" in md
    assert (tmp_path / "combined_report.json").exists()


def test_graceful_when_no_results(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(GENERATE), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    assert proc.returncode == 0
    assert "No result.json files found" in proc.stdout
