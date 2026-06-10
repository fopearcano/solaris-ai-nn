"""Tests for the language trace demo experiment."""

from __future__ import annotations

import time
from pathlib import Path

from solaris_ai_nn.experiments.language_trace_demo import run_language_trace_demo


def test_demo_runs_bounded(tmp_path):
    start = time.perf_counter()
    result = run_language_trace_demo(steps=60, state_dir=str(tmp_path / "demo"),
                                     seed=7)
    assert time.perf_counter() - start < 60.0
    assert result.steps == 60
    assert result.meaning_atoms > 0


def test_report_files_created(tmp_path):
    result = run_language_trace_demo(steps=50, state_dir=str(tmp_path / "demo"),
                                     seed=7)
    assert Path(result.report_json_path).exists()
    assert Path(result.report_md_path).exists()
    assert result.report_preview.startswith("# Solaris-AI-NN session report")


def test_explanations_contain_concrete_fields(tmp_path):
    result = run_language_trace_demo(steps=60, state_dir=str(tmp_path / "demo"),
                                     seed=7)
    assert "signal" in result.explanations["last_event"].lower()
    assert "confidence" in result.explanations["action_suggestion"]
    assert "weight" in result.explanations["strongest_habit"]
    assert "Inner MAP tracks" in result.explanations["inner_map"]


def test_embodied_demo_runs(tmp_path):
    result = run_language_trace_demo(steps=40, state_dir=str(tmp_path / "emb"),
                                     seed=5, embodied=True)
    assert result.meaning_atoms > 0
    assert "action_result" in result.explanations
    assert Path(result.report_md_path).exists()
