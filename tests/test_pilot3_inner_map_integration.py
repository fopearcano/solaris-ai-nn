"""Pilot-3 <-> Inner MAP: model field + state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_model_has_pilot3_field():
    assert InnerMapModel().pilot3 is None


def test_observer_populates_pilot3():
    class _Pilot3:
        def pilot3_status(self):
            return {"pilot3_soak_enabled": True,
                    "pilot3_soak_phase": "gridworld_action_soak",
                    "real_world_authority": False}

    observer = InnerMapObserver(pilot3=_Pilot3())
    model = observer.update()
    assert model.pilot3 is not None
    assert model.pilot3["pilot3_soak_phase"] == "gridworld_action_soak"
    assert model.pilot3["real_world_authority"] is False


def test_observer_accepts_dict_pilot3():
    observer = InnerMapObserver(pilot3={"pilot3_soak_enabled": True})
    model = observer.update()
    assert model.pilot3 == {"pilot3_soak_enabled": True}


def test_state_graph_has_pilot3_nodes():
    g = build_default_state_graph()
    for node in ("Pilot3Config", "Pilot3SoakProtocol",
                 "EmbodimentPreflightRunner", "Pilot3ComparativeDesign",
                 "ActionGroundingAnalyzer", "FirewallAudit",
                 "Pilot3DailyReviewBuilder", "Pilot3WeeklyReviewBuilder",
                 "EmbodiedPostAnalyzer", "Pilot3SoakReportBuilder",
                 "Pilot3SoakDecisionGate", "Pilot3SoakSafetyValidator"):
        assert node in g.nodes


def test_state_graph_pilot3_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("action_ledger", "FirewallAudit") in pairs
    assert ("FirewallAudit", "Pilot3SoakDecisionGate") in pairs
