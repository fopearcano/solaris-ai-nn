"""Tests that the LLM is excluded from executive authority."""

from __future__ import annotations

import inspect

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def test_llm_output_does_not_create_action_candidate(tmp_path):
    executive = ExecutiveLayer()
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={"executive": executive,
                    "ops_status": {"steps": 1, "health_level": "ok"}})
    # Paraphrased queries and assisted classifications, but the queue
    # stays empty: no LLM path touches the executive.
    gateway.handle_input("status")
    gateway.handle_input("err hmm the status maybe")
    assert len(executive.queue) == 0
    assert executive.decisions == 0


def test_llm_output_does_not_affect_arbitration(tmp_path):
    executive_plain = ExecutiveLayer()
    executive_llm = ExecutiveLayer()
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={"executive": executive_llm,
                    "ops_status": {"steps": 1}})
    gateway.handle_input("status")  # paraphrase happened
    desires = [DesireCandidate(proposal="rest", motivation=0.6,
                               confidence=0.6)]
    a = executive_plain.decide(desires, context={}, step=1)
    b = executive_llm.decide(desires, context={}, step=1)
    assert a.selected.label == b.selected.label
    assert a.scores[0].total == b.scores[0].total  # identical scoring


def test_no_llm_reference_in_executive_source():
    """Structural: the executive package never imports the adapter."""
    import solaris_ai_nn.executive.arbitration as arbitration
    import solaris_ai_nn.executive.coordinator as coordinator

    for module in (coordinator, arbitration):
        source = inspect.getsource(module)
        assert "llm" not in source.lower(), module.__name__


def test_classification_assist_cannot_create_commands(tmp_path):
    executive = ExecutiveLayer()
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={"executive": executive,
                    "ops_status": {"steps": 1}})
    # Ambiguous text that an over-eager assistant might read as a
    # command resolves to a read-only query or unknown -- never to a
    # command, an approval, or an executive candidate.
    response = gateway.handle_input("hmm maybe do the thing blorp?")
    assert response.kind in ("unknown", "status")
    assert len(executive.queue) == 0
