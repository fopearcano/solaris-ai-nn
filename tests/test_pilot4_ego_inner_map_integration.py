"""Pilot-4 <-> Ego / Inner MAP: planning-artifact attribution + state/graph."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import OwnershipAttributor
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_ego_classifies_dossier_as_planning_artifact():
    attr = OwnershipAttributor()
    result = attr.attribute_event({"origin": "pilot4_readiness_dossier"})
    assert result.category == "planning_artifact"
    assert any("not action authority" in r for r in result.reasons)


def test_ego_classifies_risk_model_and_consent():
    attr = OwnershipAttributor()
    assert attr.attribute_event(
        {"origin": "risk_model"}).category == "planning_artifact"
    assert attr.attribute_event(
        {"origin": "consent_template"}).category == "planning_artifact"


def test_model_has_pilot4_field():
    assert InnerMapModel().pilot4 is None


def test_observer_populates_pilot4():
    observer = InnerMapObserver(pilot4={
        "pilot4_planning_enabled": True,
        "current_planning_phase": "risk_assessment",
        "real_world_actuation_enabled": False,
        "readiness_conclusion": "not_ready_for_real_actuation"})
    model = observer.update()
    assert model.pilot4 is not None
    assert model.pilot4["real_world_actuation_enabled"] is False
    assert model.pilot4["readiness_conclusion"] == \
        "not_ready_for_real_actuation"


def test_state_graph_has_pilot4_nodes():
    g = build_default_state_graph()
    for node in ("Pilot4PlanningProtocol", "ActuatorTaxonomy",
                 "ForbiddenActuatorRegistry", "FutureActuatorInterfaceSpec",
                 "RiskModel", "ConsentBoundary", "ExternalAuthorityModel",
                 "ThreatModel", "HardwareIsolationPlan",
                 "FutureApprovalWorkflow", "EmergencyRequirementSet",
                 "AuditChecklist", "Pilot4ReadinessDossierBuilder",
                 "Pilot4DecisionGate", "Pilot4PlanningSafetyValidator"):
        assert node in g.nodes


def test_state_graph_pilot4_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("RiskModel", "Pilot4ReadinessDossierBuilder") in pairs
    assert ("Pilot4ReadinessDossierBuilder", "Pilot4DecisionGate") in pairs
    assert ("ConsentBoundary", "ExternalAuthorityModel") in pairs
