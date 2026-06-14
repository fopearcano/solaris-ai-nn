"""Research <-> Communication: usefulness grounded; harmful honest; safe."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    InputKind,
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.query_router import AVAILABLE_QUERIES, QueryRouter


def _route(text, components=None):
    cls = OperatorInputClassifier().classify(text)
    return cls, QueryRouter(components=components or {}).route_query(cls)


def test_module_usefulness_query_grounded():
    class _RL:
        def research_lab_status(self):
            return {"positive_modules": ["enable_world_model"]}

    cls, resp = _route("which modules actually helped?", {"research_lab": _RL()})
    assert cls.kind == InputKind.STATE_QUERY
    assert cls.args["topic"] == "rl_helped"
    assert "enable_world_model" in resp.text


def test_harmful_module_query_honest():
    class _RL:
        def research_lab_status(self):
            return {"harmful_module_candidates": ["enable_latent_replay"]}

    cls, resp = _route("which modules were harmful?", {"research_lab": _RL()})
    assert cls.args["topic"] == "rl_harmful"
    assert "enable_latent_replay" in resp.text


def test_consciousness_benchmark_query_safe():
    cls, resp = _route("is this a consciousness benchmark?")
    assert cls.args["topic"] == "rl_is_consciousness"
    text = resp.text.lower()
    assert "no" in text
    assert "do not measure or prove consciousness" in text


def test_beat_baseline_query():
    cls = OperatorInputClassifier().classify("did the full system beat the "
                                             "baseline?")
    assert cls.args["topic"] == "rl_beat_baseline"


def test_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "which modules actually helped" in joined
    assert "is this a consciousness benchmark" in joined
