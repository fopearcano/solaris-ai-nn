"""Safety <-> Communication: actuation / disable / hide queries answered safely."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    InputKind,
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.query_router import AVAILABLE_QUERIES, QueryRouter


def _route(text, components=None):
    cls = OperatorInputClassifier().classify(text)
    return cls, QueryRouter(components=components or {}).route_query(cls)


def test_real_world_actuation_query_safe():
    cls, resp = _route("is real-world actuation still blocked?")
    assert cls.kind == InputKind.STATE_QUERY
    assert cls.args["topic"] == "sf_actuation_blocked"
    text = resp.text.lower()
    assert "blocked" in text and "critical" in text


def test_disable_safety_query_safe():
    cls, resp = _route("can safety checks be disabled?")
    assert cls.args["topic"] == "sf_can_disable"
    text = resp.text.lower()
    assert "no" in text
    assert "cannot disable" in text


def test_failed_evidence_hidden_query_safe():
    cls, resp = _route("can failed safety evidence be hidden?")
    assert cls.args["topic"] == "sf_can_hide"
    text = resp.text.lower()
    assert "no" in text and "append-only" in text


def test_boundaries_protected_query():
    cls, resp = _route("what boundaries are protected?")
    assert cls.args["topic"] == "sf_boundaries"
    assert "firewall" in resp.text.lower()


def test_pilot4_still_planning_only_query():
    cls, resp = _route("is Pilot-4 still planning-only?")
    assert cls.args["topic"] == "sf_pilot4_planning"
    assert "planning-only" in resp.text.lower()


def test_invariants_passing_query_grounded():
    class _Safety:
        def safety_invariant_status(self):
            return {"critical_failure_count": 0}

    cls, resp = _route("are the safety invariants passing?",
                       {"safety_invariants": _Safety()})
    assert cls.args["topic"] == "sf_passing"
    assert "passing" in resp.text.lower()


def test_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "safety invariants passing" in joined
    assert "safety checks be disabled" in joined
