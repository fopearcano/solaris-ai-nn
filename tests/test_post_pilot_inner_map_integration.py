"""Post-pilot <-> Inner MAP: model field, observer wiring, state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

_NODES = (
    "pilot_artifact_loader", "baseline_comparator",
    "structural_change_analyzer", "accumulation_vs_growth_analyzer",
    "developmental_trace_auditor", "developmental_evidence_ledger",
    "regression_analyzer", "reproducibility_packager", "phase2_decision_gate",
    "research_dossier_builder", "post_pilot_report_builder",
    "post_pilot_safety_validator",
)


def test_model_has_post_pilot_field():
    assert hasattr(InnerMapModel(), "post_pilot")
    assert InnerMapModel().post_pilot is None


def test_state_graph_has_twelve_post_pilot_nodes():
    g = build_default_state_graph()
    for node in _NODES:
        assert node in g.nodes, node


def test_state_graph_links_post_pilot_to_inner_map():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("post_pilot_report_builder", "inner_map") in edges


def test_observer_reports_post_pilot_status():
    status = {"growth_classification": "weak_growth_evidence",
              "phase2_recommendation": "repeat_pilot1",
              "artifact_completeness": 0.8}
    model = InnerMapObserver(post_pilot=status).update()
    assert model.post_pilot is not None
    assert model.post_pilot["growth_classification"] == "weak_growth_evidence"
