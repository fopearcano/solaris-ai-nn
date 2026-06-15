"""Organismic demo <-> Operator console + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.operator_console import ProfileCatalog


def test_operator_lists_demo_profile():
    catalog = ProfileCatalog()
    ids = {e.profile_id for e in catalog.entries()}
    assert "minimal_field_organism_demo" in ids
    entry = catalog.get("minimal_field_organism_demo")
    assert entry.external_authority is False


def test_inner_map_model_has_demo_field():
    assert InnerMapModel().organismic_demo is None


def test_inner_map_includes_latest_demo_state():
    observer = InnerMapObserver(organismic_demo={
        "organismic_demo_enabled": True, "latest_demo_run_id": "OFD_x",
        "changed_perception_score": 0.8, "active_receptor_count": 8,
        "cross_modal_relation_count": 12, "proto_symbol_candidate_count": 5})
    model = observer.update()
    assert model.organismic_demo is not None
    assert model.organismic_demo["changed_perception_score"] == 0.8
    assert model.organismic_demo["latest_demo_run_id"] == "OFD_x"


def test_state_graph_has_demo_nodes():
    g = build_default_state_graph()
    for node in ("OrganismicDemoScenario", "MinimalFieldOrganismRunner",
                 "ObservationTrace", "PerceptionChangeProbe",
                 "OrganismicDemoComparison",
                 "MinimalFieldOrganismDemoReportBuilder",
                 "OrganismicDemoSafetyValidator"):
        assert node in g.nodes
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("MinimalFieldOrganismRunner", "PerceptionChangeProbe") in pairs
    assert ("MinimalFieldOrganismRunner", "inner_map") in pairs
