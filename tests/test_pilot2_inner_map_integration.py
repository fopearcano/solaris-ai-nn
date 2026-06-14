"""Pilot-2 <-> Inner MAP: model field, observer wiring, state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

_NODES = (
    "pilot2_protocol", "pilot2_config", "source_preflight_runner",
    "source_curation_report", "exposure_schedule", "comparative_run_design",
    "grounding_analysis", "source_reliability_monitor",
    "pilot2_daily_review_builder", "pilot2_weekly_review_builder",
    "pilot2_report_builder", "pilot2_decision_gate", "pilot2_runbook_builder",
    "pilot2_safety_validator",
)


def test_model_has_pilot2_field():
    assert hasattr(InnerMapModel(), "pilot2")
    assert InnerMapModel().pilot2 is None


def test_state_graph_has_fourteen_pilot2_nodes():
    g = build_default_state_graph()
    for node in _NODES:
        assert node in g.nodes, node


def test_state_graph_links_pilot2_to_inner_map():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("pilot2_protocol", "inner_map") in edges


def test_observer_reports_pilot2_status():
    status = {"pilot2_enabled": True, "pilot2_phase": "fixture_short_run",
              "source_mode": "mixed_nursery_and_membrane"}
    model = InnerMapObserver(pilot2=status).update()
    assert model.pilot2 is not None
    assert model.pilot2["pilot2_phase"] == "fixture_short_run"
