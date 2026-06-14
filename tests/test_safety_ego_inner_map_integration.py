"""Safety <-> Ego / Inner MAP: inert classification + state/graph nodes."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import OwnershipAttributor
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_ego_classifies_red_team_fixture_as_inert():
    attr = OwnershipAttributor()
    result = attr.attribute_event({"origin": "red_team_fixture"})
    assert result.category == "red_team_fixture"
    assert any("inert" in r for r in result.reasons)
    assert result.is_executable_instruction is False


def test_ego_classifies_assurance_and_invariant():
    attr = OwnershipAttributor()
    assert attr.attribute_event(
        {"origin": "assurance_case"}).category == "assurance_claim"
    assert attr.attribute_event(
        {"origin": "safety_invariant"}).category == "safety_invariant_result"


def test_model_has_safety_field():
    assert InnerMapModel().safety_invariants is None


def test_observer_populates_safety():
    observer = InnerMapObserver(safety_invariants={
        "safety_invariant_runner_enabled": True, "critical_failure_count": 0,
        "unresolved_blocker_count": 0})
    model = observer.update()
    assert model.safety_invariants is not None
    assert model.safety_invariants["critical_failure_count"] == 0


def test_state_graph_has_safety_nodes():
    g = build_default_state_graph()
    for node in ("SafetyInvariantRegistry", "SafetyInvariantRunner",
                 "RedTeamHarness", "AdversarialFixtureFactory",
                 "BoundaryRegressionSuite", "SafetyEvidenceLedger",
                 "AssuranceCaseCompiler", "SafetyFailureTriage",
                 "SafetyInvariantDashboard", "SafetyInvariantSystemValidator"):
        assert node in g.nodes


def test_state_graph_safety_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("SafetyEvidenceLedger", "AssuranceCaseCompiler") in pairs
    assert ("RedTeamHarness", "SafetyEvidenceLedger") in pairs
