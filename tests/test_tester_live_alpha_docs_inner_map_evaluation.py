"""Tester live alpha/docs/inner-map/evaluation: status, docs, record, metrics."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_alpha_exposes_tester_live_status(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    alpha = AlphaResearchOrchestrator()
    status = alpha.tester_live_status(
        tester_live_state_dir=str(tmp_path / "tester"))
    assert status["tester_live_available"] is True
    assert status["live_read_only"] is True
    assert status["starts_feeders"] is False
    assert status["learns"] is False


def test_alpha_absent_without_state(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    alpha = AlphaResearchOrchestrator()
    status = alpha.tester_live_status(
        tester_live_state_dir=str(tmp_path / "none"))
    assert status["tester_live_available"] is False


def test_inner_map_record(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    rec = rt.inner_map_record()
    assert rec["tester_live_run_id"]
    assert rec["live_read_only"] is True
    assert rec["trains_on_feedback"] is False
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_live_readonly = rec
    assert m.to_dict()["tester_live_readonly"]["tester_live_run_id"]


def test_evaluation_metrics_computed(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    from solaris_ai_nn.evaluation.metrics import tester_live_readonly_metrics
    metrics = tester_live_readonly_metrics(rt.tester_live_status())
    assert metrics["present"] is True
    assert metrics["live_read_only"] is True
    assert metrics["starts_feeders"] is False


def test_docs_include_tester_live_path():
    for rel in ("README.md", os.path.join("docs", "ARCHITECTURE.md")):
        text = open(os.path.join(_ROOT, rel)).read().lower()
        assert "tester live-read-only" in text, rel
