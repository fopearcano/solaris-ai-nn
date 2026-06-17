"""Tester alpha/docs/inner-map/evaluation: status exposed, docs, record, metrics."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_alpha_exposes_tester_status(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    alpha = AlphaResearchOrchestrator()
    status = alpha.tester_fixture_status(tester_state_dir=str(tmp_path))
    assert status["tester_demo_available"] is True
    assert status["reproducibility_status"] in (
        "pass", "pass_with_warnings", "fail", "blocked", "inconclusive")
    assert status["learns"] is False
    assert status["controls_feeders"] is False


def test_alpha_absent_without_tester_state(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    alpha = AlphaResearchOrchestrator()
    status = alpha.tester_fixture_status(tester_state_dir=str(tmp_path / "none"))
    assert status["tester_demo_available"] is False


def test_inner_map_record(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    rec = rt.inner_map_record()
    assert rec["tester_demo_run_id"]
    assert rec["fixture_only"] is True
    assert rec["trains_on_feedback"] is False
    # Inner map model accepts the field.
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_fixture_spine = rec
    assert m.to_dict()["tester_fixture_spine"]["tester_demo_run_id"]


def test_evaluation_metrics_computed(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    from solaris_ai_nn.evaluation.metrics import tester_fixture_spine_metrics
    metrics = tester_fixture_spine_metrics(rt.tester_status())
    assert metrics["present"] is True
    assert metrics["tester_fixture_event_count"] >= 14
    assert metrics["tester_fixture_quarantined_count"] >= 1
    assert metrics["requires_live_data"] is False


def test_docs_include_tester_section():
    for rel in ("README.md", os.path.join("docs", "ARCHITECTURE.md")):
        text = open(os.path.join(_ROOT, rel)).read().lower()
        assert "tester fixture spine" in text, rel
