"""Publication dossier: generated, includes negative/inconclusive, readiness."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    ForbiddenClaimDetector,
    PublicationDossierBuilder,
    PublicationReadinessStatus,
)


def _registry(claims):
    return {"claims": claims, "scientific_claim_count": len(claims),
            "note": "registry note"}


def _supported():
    return {"claim_id": "c1", "text": "x", "category": "sensorium_claim",
            "status": "supported", "evidence_refs": ["e1"],
            "counterevidence_refs": [], "strength": "strong"}


def _empty_aux():
    return ({"mapping": {}}, {"records": [], "blocking_counterevidence_count": 0},
            {"limitations": [], "limitation_count": 4})


def test_dossier_generated():
    em, ce, lim = _empty_aux()
    forbidden = ForbiddenClaimDetector.summary([])
    dossier = PublicationDossierBuilder().build(
        claim_registry=_registry([_supported()]), evidence_map=em,
        counterevidence=ce, forbidden=forbidden, limitations=lim)
    d = dossier.to_dict()
    assert d["is_release"] is False and d["is_draft"] is True
    assert "abstract" in d["sections"]
    assert "safety_boundaries" in d["sections"]


def test_negative_and_inconclusive_included():
    em, ce, lim = _empty_aux()
    claims = [_supported(),
              {"claim_id": "c2", "text": "neg", "category": "negative_result_claim",
               "status": "unsupported", "evidence_refs": [],
               "counterevidence_refs": [], "strength": "none"},
              {"claim_id": "c3", "text": "inc", "category": "inconclusive_claim",
               "status": "inconclusive", "evidence_refs": ["e2"],
               "counterevidence_refs": [], "strength": "inconclusive"}]
    dossier = PublicationDossierBuilder().build(
        claim_registry=_registry(claims), evidence_map=em, counterevidence=ce,
        forbidden=ForbiddenClaimDetector.summary([]), limitations=lim)
    sec = dossier.sections
    assert sec["negative_results"]
    assert sec["inconclusive_results"]


def test_readiness_blocked_by_forbidden_claims():
    em, ce, lim = _empty_aux()
    forbidden = ForbiddenClaimDetector.summary(
        ForbiddenClaimDetector().scan("Solaris is conscious."))
    dossier = PublicationDossierBuilder().build(
        claim_registry=_registry([_supported()]), evidence_map=em,
        counterevidence=ce, forbidden=forbidden, limitations=lim)
    assert dossier.readiness == \
        PublicationReadinessStatus.BLOCKED_BY_FORBIDDEN_CLAIMS


def test_readiness_blocked_by_safety():
    em, ce, lim = _empty_aux()
    dossier = PublicationDossierBuilder().build(
        claim_registry=_registry([_supported()]), evidence_map=em,
        counterevidence=ce, forbidden=ForbiddenClaimDetector.summary([]),
        limitations=lim, safety_failed=True)
    assert dossier.readiness == PublicationReadinessStatus.BLOCKED_BY_SAFETY
