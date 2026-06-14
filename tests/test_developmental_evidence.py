"""Post-pilot developmental evidence ledger: refs, grading, contradictions."""

from __future__ import annotations

import pytest

from solaris_ai_nn.post_pilot import (
    ClaimType,
    DevelopmentalEvidenceLedger,
    EvidenceStrength,
)


def test_claim_requires_evidence_refs():
    ledger = DevelopmentalEvidenceLedger()
    claim = ledger.add(ClaimType.MEMORY_CONSOLIDATED, evidence_refs=[])
    assert claim.strength == EvidenceStrength.UNSUPPORTED


def test_single_ref_is_weak():
    ledger = DevelopmentalEvidenceLedger()
    claim = ledger.add(ClaimType.HABIT_FORMED, evidence_refs=["e1"],
                       artifact_types=["conscience_bus"])
    assert claim.strength == EvidenceStrength.WEAK


def test_strong_claim_requires_multiple_artifact_types():
    ledger = DevelopmentalEvidenceLedger()
    claim = ledger.add(ClaimType.WORLD_MODEL_CHANGED, evidence_refs=["e1"],
                       artifact_types=["conscience_bus", "hypothesis_history"])
    assert claim.strength == EvidenceStrength.STRONG


def test_persistent_claim_is_strong():
    ledger = DevelopmentalEvidenceLedger()
    claim = ledger.add(ClaimType.PROTO_SYMBOL_STABILIZED,
                       evidence_refs=["e1"], artifact_types=["proto_symbols"],
                       persistent=True)
    assert claim.strength == EvidenceStrength.STRONG


def test_contradicted_claim_highlighted():
    ledger = DevelopmentalEvidenceLedger()
    ledger.add(ClaimType.REGRESSION_DETECTED, evidence_refs=["e1"],
               contradicted=True)
    assert ledger.contradicted_claims()
    assert ledger.snapshot()["contradicted"]


def test_unknown_claim_type_rejected():
    with pytest.raises(ValueError):
        DevelopmentalEvidenceLedger().add("not_a_claim")


def test_from_structural_evidence():
    from solaris_ai_nn.post_pilot import StructuralChangeEvidence

    ledger = DevelopmentalEvidenceLedger()
    ev = StructuralChangeEvidence(
        category="memory_reorganization", metric_delta=0.3,
        supporting_artifacts=["developmental_state", "autobiographical_memory"],
        stability="persistent")
    claims = ledger.from_structural_evidence([ev])
    assert claims and claims[0].claim_type == ClaimType.MEMORY_CONSOLIDATED
