"""Pilot-4 <-> Communication: device refused; readiness grounded; safe approval."""

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


def test_device_control_query_refused():
    cls, resp = _route("can Solaris control devices now?")
    assert cls.kind == InputKind.STATE_QUERY
    assert cls.args["topic"] == "p4_control_devices_now"
    text = resp.text.lower()
    assert "no" in text and "planning-only" in text and "prohibited" in text


def test_connect_robot_query_refused():
    cls, resp = _route("can we connect a robot?")
    assert cls.args["topic"] == "p4_connect_robot"
    assert "prohibited" in resp.text.lower()


def test_real_world_actuation_enabled_query():
    cls, resp = _route("is real-world actuation enabled?")
    assert cls.args["topic"] == "p4_actuation_enabled"
    assert "no" in resp.text.lower()


def test_planning_approval_confusion_answered_safely():
    cls, resp = _route("is Pilot-4 approval to use actuators?")
    assert cls.args["topic"] == "p4_is_approval"
    text = resp.text.lower()
    assert "not approval" in text or "planning" in text


def test_readiness_query_grounded():
    class _Pilot4:
        def pilot4_status(self):
            return {"readiness_conclusion": "not_ready_for_real_actuation"}

    cls, resp = _route("what is the current readiness conclusion?",
                       {"pilot4": _Pilot4()})
    assert cls.args["topic"] == "p4_readiness"
    assert "not_ready_for_real_actuation" in resp.text


def test_required_before_actuation_query():
    cls, resp = _route("what would be required before real actuation?")
    assert cls.args["topic"] == "p4_required"
    assert "governance" in resp.text.lower()


def test_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "real-world actuation enabled" in joined
    assert "connect a robot" in joined
