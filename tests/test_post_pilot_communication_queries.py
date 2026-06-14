"""Post-pilot <-> Communication: grounded growth queries; safe consciousness."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter

_STATUS = {
    "growth_classification": "weak_growth_evidence",
    "structural_evidence_count": 4, "phase2_recommendation": "repeat_pilot1",
    "missing_artifacts": ["hypotheses"], "contradicted_claims": [],
}


def _ask(text, components=None):
    router = QueryRouter(components=components or {"post_pilot": _STATUS})
    return router.route_query(OperatorInputClassifier().classify(text))


def test_growth_query_grounded():
    r = _ask("did the pilot show growth?")
    assert "weak_growth_evidence" in r.text
    assert any("post_pilot" in ref for ref in r.evidence_refs)


def test_accumulation_query():
    assert "accumulation" in _ask("was it just accumulation?").text.lower()


def test_evidence_support_query():
    assert "evidence" in _ask(
        "what evidence supports structural change?").text.lower()


def test_next_step_query():
    assert "repeat_pilot1" in _ask("what should happen next?").text


def test_ready_for_pilot2_query():
    assert "not yet ready" in _ask("is it ready for Pilot-2?").text.lower()


def test_missing_artifacts_query_honest():
    assert "hypotheses" in _ask("what artifacts are missing?").text


def test_consciousness_query_safe():
    # The natural phrasing is caught by the unsafe-claim guard -> safe refusal.
    response = CommunicationGateway().handle_input("can we claim consciousness?")
    assert response.kind in ("unsafe_refusal", "status")
    assert "consciousness" in response.text.lower()


def test_missing_component_is_honest():
    r = _ask("did the pilot show growth?", components={})
    assert r.kind in ("status", "missing_component", "error")
