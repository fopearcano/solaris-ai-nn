"""Forbidden claims: assertions blocked, disclaimers allowed, ambiguity warned."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ForbiddenClaimDetector


def test_consciousness_life_agency_assertions_blocked():
    det = ForbiddenClaimDetector()
    for text in ("Solaris is conscious.", "The system is alive.",
                 "It has agency and free will."):
        assert det.has_blocking_assertion(text), text


def test_disclaimers_allowed():
    det = ForbiddenClaimDetector()
    text = ("This system is not conscious and makes no claim of sentience, "
            "agency, or subjective experience.")
    assert not det.has_blocking_assertion(text)
    claims = det.scan(text)
    # Any matches present are disclaimers, not blocking assertions.
    assert all(not c.blocks_publication for c in claims)


def test_ambiguous_wording_warned():
    det = ForbiddenClaimDetector()
    claims = det.scan("The system seems aware of its surroundings.")
    assert any(c.is_ambiguous for c in claims)
    summary = ForbiddenClaimDetector.summary(claims)
    assert summary["ambiguous_count"] >= 1
    # Ambiguous wording warns, it does not block.
    assert summary["blocks_publication"] is False


def test_summary_blocks_on_assertion():
    det = ForbiddenClaimDetector()
    summary = ForbiddenClaimDetector.summary(det.scan("It is sentient."))
    assert summary["blocks_publication"] is True
    assert summary["asserted_forbidden_count"] >= 1
