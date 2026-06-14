"""Motor <-> Communication: motor membrane queries classify and route safely."""

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


def test_device_control_answered_safely_with_no_component():
    cls, resp = _route("can pilot-3 control devices?")
    assert cls.kind == InputKind.STATE_QUERY
    assert cls.args["topic"] == "mm_devices"
    text = resp.text.lower()
    assert "no" in text and "simulation" in text


def test_real_world_action_answered_safely():
    cls, resp = _route("is solaris acting on the real world?")
    assert cls.args["topic"] == "mm_acting"
    assert "no" in resp.text.lower()
    assert "firewall" in resp.text.lower()


def test_motor_queries_classify():
    c = OperatorInputClassifier()
    cases = {
        "what actions were proposed?": "mm_proposed",
        "what actions were vetoed?": "mm_vetoed",
        "what simulated action happened?": "mm_simulated",
        "what did the firewall block?": "mm_firewall",
        "current embodiment profile?": "mm_profile",
        "is this real action or simulated action?": "mm_real_or_sim",
    }
    for text, topic in cases.items():
        assert c.classify(text).args.get("topic") == topic, text


def test_component_backed_answer():
    class _Stub:
        def summary(self):
            return {"action_count": 7, "veto_count": 2,
                    "blocked_real_world_count": 1, "profile_id": "gridworld",
                    "firewall_enabled": True}

    _, resp = _route("what actions were vetoed?",
                     {"motor_membrane": _Stub()})
    assert "2" in resp.text


def test_unsafe_phrasings_caught_first():
    # "robot"/"actuator" hit the unsafe rule before the motor state query.
    c = OperatorInputClassifier()
    assert c.classify("can you move a robot arm?").kind == \
        InputKind.UNSAFE_REQUEST


def test_motor_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "control devices" in joined
    assert "real world" in joined
