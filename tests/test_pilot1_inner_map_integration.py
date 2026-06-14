"""Pilot-1 <-> Inner MAP: model field, observer wiring, state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

_PILOT_NODES = (
    "pilot_protocol", "pilot_config", "pilot_observability_collector",
    "pilot_health_dashboard", "resource_budget_monitor", "retention_policy",
    "daily_review_builder", "weekly_review_builder", "restart_drill_runner",
    "failure_mode_detector", "pilot_exit_criteria", "operator_runbook_builder",
    "pilot_report_builder", "pilot_safety_validator",
)


def test_model_has_pilot_field():
    assert hasattr(InnerMapModel(), "pilot1")
    assert InnerMapModel().pilot1 is None


def test_state_graph_has_fourteen_pilot_nodes():
    g = build_default_state_graph()
    for node in _PILOT_NODES:
        assert node in g.nodes, node


def test_state_graph_links_pilot_report_to_inner_map():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("pilot_report_builder", "inner_map") in edges


def test_observer_reports_pilot_status():
    pilot_status = {"pilot1_enabled": True, "pilot_mode": "plan_only",
                    "pilot_phase": "preflight", "exit_recommendation":
                    "continue"}
    observer = InnerMapObserver(pilot1=pilot_status)
    model = observer.update()
    assert model.pilot1 is not None
    assert model.pilot1["pilot_phase"] == "preflight"
