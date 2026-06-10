"""Tests for language artifacts via the ContinuousRunner."""

from __future__ import annotations

import json
import time

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner


def test_bounded_run_saves_language_artifacts(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(state_dir=tmp_path / "lang", max_steps=50,
                              checkpoint_interval_steps=25,
                              enable_language=True, report_interval_steps=20,
                              seed=5)
    snap = runner.run()
    assert time.perf_counter() - start < 60.0  # no infinite loop
    pm = runner.pm
    for path in (pm.meaning_trace_path, pm.causal_trace_path,
                 pm.session_report_json_path, pm.session_report_md_path,
                 pm.last_explanations_path):
        assert path.exists(), path
    # Report content is real JSON with the standard sections.
    data = json.loads(pm.session_report_json_path.read_text())
    assert data["sections"]["runtime"]["steps"] == 50
    assert data["limitations"]
    # Snapshot exposes the language view.
    assert snap["language"]["enabled"] is True
    assert snap["language"]["meaning_atoms"] > 0
    assert snap["language"]["last_event_explanation"]["text"]


def test_language_disabled_runner_unchanged(tmp_path):
    runner = ContinuousRunner(state_dir=tmp_path / "plain", max_steps=20, seed=5)
    snap = runner.run()
    assert "language" not in snap
    assert not runner.pm.session_report_md_path.exists()
