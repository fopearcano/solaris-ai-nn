"""Pilot-2 <-> Communication: reliability/action/source-mode queries."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter

_STATUS = {"pilot2_enabled": True, "pilot2_phase": "mixed_nursery_membrane_run",
           "reliable_source_count": 2, "source_disable_count": 1,
           "latest_grounding_quality": "moderate",
           "source_mode": "mixed_nursery_and_membrane",
           "recommendation": "extend_read_only_soak"}


def _ask(text, components=None):
    router = QueryRouter(components=components or {"pilot2": _STATUS})
    return router.route_query(OperatorInputClassifier().classify(text))


def test_source_reliability_query_grounded():
    r = _ask("which sources are reliable?")
    assert "reliable sources" in r.text
    assert any("pilot2" in ref for ref in r.evidence_refs)


def test_environment_action_query_safe():
    r = _ask("is Solaris acting on the environment?", components={})
    assert "No. Pilot-2 is read-only" in r.text
    assert "no authority to modify, control, or act" in r.text


def test_real_simulated_source_mode_query_grounded():
    assert "real read-only" in _ask(
        "is this real, simulated, fixture, or nursery input?").text


def test_pilot2_phase_query():
    assert "mixed_nursery_membrane_run" in _ask(
        "what Pilot-2 phase is active?").text


def test_grounding_query_cautious():
    r = _ask("did read-only input improve grounding?")
    assert "observed associations" in r.text


def test_ready_24h_query_requires_approval():
    r = _ask("is Pilot-2 ready for a 24h read-only soak?")
    assert "governance approval" in r.text
