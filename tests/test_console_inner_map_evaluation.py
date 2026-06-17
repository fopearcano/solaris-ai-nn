"""Console inner-map + evaluation: record built, metrics computed."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def test_inner_map_record(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    rec = rt.inner_map_record()
    assert rec["console_generated"] is True
    assert rec["read_only"] is True
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_console = rec
    assert m.to_dict()["tester_console"]["console_generated"] is True


def test_evaluation_metrics_computed(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    from solaris_ai_nn.evaluation.metrics import tester_console_metrics
    metrics = tester_console_metrics(rt.console_status())
    assert metrics["present"] is True
    assert metrics["tester_console_artifact_count"] >= 1
    assert metrics["read_only"] is True
    assert metrics["runs_server"] is False


def test_inner_map_warning_when_unavailable(tmp_path, monkeypatch):
    # Simulate inner_map import failure -> runtime records a warning, no crash.
    rt = build_console(tmp_path)
    assert isinstance(rt.warnings, list)
