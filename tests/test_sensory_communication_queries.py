"""Sensory <-> Communication: read-only/command/real-vs-simulated queries."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter

_STATUS = {"enabled": True, "source_count": 3, "active_source_count": 2,
           "degraded_source_count": 1, "read_only": True,
           "simulated_sources_only": False}


def _ask(text, components=None):
    router = QueryRouter(components=components or {"sensory_membrane": _STATUS})
    return router.route_query(OperatorInputClassifier().classify(text))


def test_read_only_query_safe():
    r = _ask("is the membrane read-only?")
    assert "read-only" in r.text.lower()
    assert "never acts on the world" in r.text


def test_input_command_query_safe():
    r = _ask("did sensory input become a command?", components={})
    assert "cannot become an operator command" in r.text


def test_real_vs_simulated_query_grounded():
    r = _ask("is this real or simulated input?")
    assert "read-only" in r.text.lower()
    assert any("sensory_membrane" in ref for ref in r.evidence_refs)


def test_active_sources_query():
    assert "active sensory sources" in _ask(
        "what sensory sources are active?").text


def test_degraded_sources_query():
    assert "degraded sources" in _ask("what sources are degraded?").text


def test_proto_query():
    assert "proto-symbol" in _ask(
        "what proto-symbols came from sensory input?").text
