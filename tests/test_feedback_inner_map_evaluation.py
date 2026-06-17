"""Feedback inner-map + evaluation: record built, metrics computed."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import sample_path  # noqa: E402


def test_inner_map_record(tmp_path):
    rt = TesterFeedbackRuntime(
        tester_state_dir=str(tmp_path),
        ingest_path=sample_path("sample_safety_concern.json"))
    rt.run()
    rec = rt.inner_map_record()
    assert rec["feedback_system_initialized"] is True
    assert rec["trains_on_feedback"] is False
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_feedback = rec
    assert m.to_dict()["tester_feedback"]["feedback_system_initialized"] is True


def test_evaluation_metrics_computed(tmp_path):
    rt = TesterFeedbackRuntime(
        tester_state_dir=str(tmp_path),
        ingest_path=sample_path("sample_bug_report.json"))
    rt.run()
    from solaris_ai_nn.evaluation.metrics import tester_feedback_metrics
    metrics = tester_feedback_metrics(rt.feedback_status())
    assert metrics["present"] is True
    assert metrics["tester_feedback_entry_count"] >= 1
    assert metrics["trains_on_feedback"] is False
    assert metrics["is_rlhf"] is False


def test_inner_map_warning_when_unavailable(tmp_path):
    rt = TesterFeedbackRuntime(tester_state_dir=str(tmp_path))
    rt.run()
    assert isinstance(rt.warnings, list)
