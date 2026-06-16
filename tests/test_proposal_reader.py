"""Proposal reader: variant read, unsafe blocked, inconclusive -> retest."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import ArchitectureProposalReader
from solaris_ai_nn.experiment_compiler.proposal_reader import ProposalDisposition


def test_variant_proposal_read():
    read = ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_sensorium_profiles",
        "proposal": "broaden source diet", "reason": "fixture overfit",
        "evidence_refs": ["replication:overfit"]})
    assert read.proposal_id == "p1"
    assert read.target_label == "revise_sensorium_profiles"
    assert read.evidence_refs == ["replication:overfit"]
    assert read.disposition == ProposalDisposition.IMPLEMENTABLE


def test_unsafe_proposal_blocked():
    read = ArchitectureProposalReader().read({
        "proposal_id": "p2", "target": "actuate robot arm", "safe": False})
    assert read.disposition == ProposalDisposition.BLOCKED_UNSAFE


def test_falsified_proposal_blocked():
    read = ArchitectureProposalReader().read({
        "proposal_id": "p3", "target": "promote X", "blocks_promotion": True})
    assert read.disposition == ProposalDisposition.BLOCKED_FALSIFIED


def test_inconclusive_proposal_becomes_retest():
    read = ArchitectureProposalReader().read({
        "proposal_id": "p4", "target": "revise_cognition",
        "inconclusive": True, "missing_evidence": ["more runs"]})
    assert read.disposition == ProposalDisposition.RETEST_INCONCLUSIVE
    assert read.missing_evidence == ["more runs"]


def test_read_all():
    reads = ArchitectureProposalReader().read_all([
        {"proposal_id": "a", "target": "x"},
        {"proposal_id": "b", "target": "y", "safe": False}])
    assert len(reads) == 2
    assert reads[1].disposition == ProposalDisposition.BLOCKED_UNSAFE
