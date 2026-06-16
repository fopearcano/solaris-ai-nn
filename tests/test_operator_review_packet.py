"""Operator review packet: generated, no self-approval, decisions serialize."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    ReviewDecision,
    ReviewPacketBuilder,
    SafetyGateEvaluator,
    compile_spec,
)


def _packet(proposal, *, gate_ok=True):
    spec = compile_spec(ArchitectureProposalReader().read(proposal))
    spec_d = spec.to_dict()
    gates = SafetyGateEvaluator()
    results = gates.evaluate(spec_d, claim_guard_ok=gate_ok)
    return ReviewPacketBuilder().build(spec_d, gate_summary=gates.summary(
        results))


def test_review_packet_generated():
    packet = _packet({"proposal_id": "p1", "target": "revise_ontogenesis",
                      "proposal": "raise threshold",
                      "evidence_refs": ["replication:ok"]})
    md = packet.render_markdown()
    assert "# Operator Review Packet" in md
    assert packet.review_questions
    assert packet.recommended_next_step


def test_no_self_approval():
    packet = _packet({"proposal_id": "p1", "target": "revise_cognition",
                      "proposal": "raise limit"})
    d = packet.to_dict()
    assert d["self_approved"] is False
    assert d["decision"] is None
    assert all(q["answer"] is None for q in d["review_questions"])


def test_decisions_serialize():
    packet = _packet({"proposal_id": "p1", "target": "revise_sensorium",
                      "proposal": "broaden diet"})
    assert set(packet.to_dict()["available_decisions"]) == set(
        ReviewDecision.ALL)


def test_critical_gate_failure_recommends_block():
    packet = _packet({"proposal_id": "p1", "target": "revise_cognition",
                      "proposal": "raise limit"}, gate_ok=False)
    assert "block_for_safety" in packet.recommended_next_step
