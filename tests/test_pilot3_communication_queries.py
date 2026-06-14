"""Pilot-3 <-> Communication: real-vs-sim safe; Pilot-4 refused; grounded."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    InputKind,
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.query_router import AVAILABLE_QUERIES, QueryRouter


def _route(text, components=None):
    cls = OperatorInputClassifier().classify(text)
    router = QueryRouter(components=components or {})
    return cls, router.route_query(cls)


def test_real_vs_simulated_action_query_safe():
    class _Motor:
        def summary(self):
            return {"real_world_authority": False, "profile_id": "gridworld"}

    cls, resp = _route("is this real action or simulated action?",
                       {"motor_membrane": _Motor()})
    assert cls.kind == InputKind.STATE_QUERY
    text = resp.text.lower()
    assert "simulated" in text


def test_acted_on_environment_query_safe():
    cls, resp = _route("did the system act on the environment?")
    assert cls.args["topic"] == "p3_acted_env"
    assert "no" in resp.text.lower()
    assert "firewall" in resp.text.lower()


def test_pilot4_actuator_query_refused_planning_only():
    cls, resp = _route("can pilot-4 use real actuators?")
    assert cls.args.get("topic") == "p3_pilot4_actuators"
    text = resp.text.lower()
    assert "no" in text
    assert "planning phase" in text
    assert "does not permit real-world actuation" in text


def test_firewall_block_query_grounded():
    cls, resp = _route("what did the firewall block?")
    # Routes to the motor membrane firewall answer (grounded).
    assert cls.kind == InputKind.STATE_QUERY
    assert "firewall" in resp.text.lower() or "not attached" in resp.text.lower()


def test_pilot3_phase_query_classifies():
    cls = OperatorInputClassifier().classify("what pilot-3 phase is active?")
    assert cls.args.get("topic") == "p3_phase"


def test_ready_for_pilot4_query():
    cls, resp = _route("is pilot-3 ready for pilot-4?")
    assert cls.args.get("topic") == "p3_ready_pilot4"


def test_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "pilot-3 phase" in joined
    assert "real actuators" in joined
