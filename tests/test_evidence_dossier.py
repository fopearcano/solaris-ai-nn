"""Evidence dossier: claims need refs, inconclusive allowed, no life claims."""

from __future__ import annotations

import pytest

from solaris_ai_nn.developmental_soak import (
    DevelopmentalEvidenceDossier,
    EvidenceClaim,
    EvidenceClaimType,
    EvidenceDossierBuilder,
    EvidenceStrength,
)


def test_claims_require_evidence_refs():
    with pytest.raises(ValueError):
        EvidenceClaim(claim_type=EvidenceClaimType.INCONCLUSIVE,
                      strength=EvidenceStrength.INCONCLUSIVE,
                      statement="no refs", evidence_refs=[])


def test_inconclusive_claim_allowed():
    dossier = DevelopmentalEvidenceDossier()
    claim = dossier.add_claim(EvidenceClaimType.INCONCLUSIVE,
                              EvidenceStrength.INCONCLUSIVE,
                              "growth is inconclusive", ["dev:status"])
    assert claim.strength == EvidenceStrength.INCONCLUSIVE
    assert dossier.to_dict()["inconclusive_claim_count"] == 1


def test_consciousness_life_claims_impossible():
    dossier = DevelopmentalEvidenceDossier()
    for forbidden in ("solaris is conscious", "it is alive",
                      "it has free will", "it has subjective experience"):
        with pytest.raises(ValueError):
            dossier.add_claim(EvidenceClaimType.STRUCTURAL_GROWTH_OBSERVED,
                              EvidenceStrength.STRONG, forbidden, ["dev:status"])


def test_builder_conservative_on_accumulation():
    dossier = EvidenceDossierBuilder().build(
        dev_status={"structural_growth_status": "mere_event_accumulation",
                    "accumulation_warning_count": 2})
    types = {c.claim_type for c in dossier.claims}
    assert EvidenceClaimType.STRUCTURAL_GROWTH_NOT_OBSERVED in types
    assert EvidenceClaimType.ACCUMULATION_WARNING in types


def test_builder_records_growth_with_evidence():
    dossier = EvidenceDossierBuilder().build(
        dev_status={"structural_growth_status": "real_structural_growth",
                    "structural_growth_score": 0.9})
    grew = [c for c in dossier.claims
            if c.claim_type == EvidenceClaimType.STRUCTURAL_GROWTH_OBSERVED]
    assert grew
    assert all(c.evidence_refs for c in dossier.claims)


def test_safety_boundary_always_claimed():
    dossier = EvidenceDossierBuilder().build(dev_status={}, safety_block_count=0)
    types = {c.claim_type for c in dossier.claims}
    assert EvidenceClaimType.SAFETY_BOUNDARY_PRESERVED in types
