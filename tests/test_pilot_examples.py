"""Subprocess tests for the Pilot-0 examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"
SAMPLES = EXAMPLES / "sample_streams"


def _run(script, *args, timeout=180):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script} too slow"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_simulated_pilot_example_runs(tmp_path):
    out = _run("run_pilot_simulated.py", "--steps", "60",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "pilots"))
    assert "readiness:       ready" in out
    assert "status:          completed" in out
    assert "recommendation:" in out
    reports = list((tmp_path / "pilots" / "runs").glob("*/pilot_report.md"))
    assert len(reports) == 1


def test_stream_pilot_example_runs_on_sample_input(tmp_path):
    out = _run("run_pilot_stream.py",
               "--input", str(SAMPLES / "sensory_events.jsonl"),
               "--format", "jsonl", "--steps", "60",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "pilots"))
    assert "status:          completed" in out
    assert "events accepted: 40" in out
    assert "events rejected: 0" in out


def test_stream_pilot_text_format(tmp_path):
    out = _run("run_pilot_stream.py",
               "--input", str(SAMPLES / "text_stream.txt"),
               "--format", "text", "--steps", "50", "--tail",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "pilots"))
    assert "tail preview" in out
    assert "status:          completed" in out


def test_fake_sidecar_pilot_example_runs_observe_only(tmp_path):
    out = _run("run_pilot_sidecar_fake.py", "--steps", "60",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "pilots"))
    assert "status:             completed" in out
    assert "suggestions published: 0" in out
    assert "conscience driven:  stimulate=0 react=0 death=0" in out


def test_readiness_example_runs(tmp_path):
    out = _run("run_pilot_readiness.py", "--profile", "simulated",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "readiness"))
    assert "verdict:   READY" in out
    assert (tmp_path / "readiness" / "readiness_report.md").exists()


def test_pilot_runbook_generation_works(tmp_path):
    for profile, expected in (("simulated", "runbook_pilot_simulated.md"),
                              ("read_only_stream",
                               "runbook_pilot_stream.md")):
        out = _run("generate_pilot_runbook.py", "--profile", profile,
                   "--output-dir", str(tmp_path / profile), timeout=60)
        assert "written to:" in out
        assert (tmp_path / profile / expected).exists()


def test_sample_streams_are_contract_clean():
    """Every sample line passes the data contracts (0 rejections)."""
    from solaris_ai_nn.pilot.stream_ingestion import ReadOnlyStreamIngestor

    ingestor = ReadOnlyStreamIngestor()
    jsonl = ingestor.read_once(SAMPLES / "sensory_events.jsonl")
    text = ingestor.read_once(SAMPLES / "text_stream.txt")
    assert len(jsonl) == 40 and len(text) == 20
    assert ingestor.events_rejected == 0
