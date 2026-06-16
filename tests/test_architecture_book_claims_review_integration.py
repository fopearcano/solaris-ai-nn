"""Architecture book <-> Scientific Claims + Independent Review integration."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    GlossaryBuilder,
    SolarisArchitectureOutlineBuilder,
    TechnicalWhitepaperBuilder,
)


def test_scientific_claims_included_if_available():
    impl = {c.module_key: c.implemented
            for c in SolarisArchitectureOutlineBuilder().build()}
    # scientific_claims is present in this repo.
    assert impl.get("scientific_claims") is True
    wp = TechnicalWhitepaperBuilder().build_whitepaper().lower()
    assert "scientific claim" in wp
    assert "forbidden" in wp


def test_independent_review_included_if_available():
    impl = {c.module_key: c.implemented
            for c in SolarisArchitectureOutlineBuilder().build()}
    assert impl.get("independent_review") is True
    wp = TechnicalWhitepaperBuilder().build_whitepaper().lower()
    assert "independent review" in wp
    assert "reproducibility" in wp


def test_claim_discipline_terms_in_glossary():
    terms = {e.term for e in GlossaryBuilder().build()}
    assert "scientific claim registry" in terms
    assert "independent review" in terms
    assert "review assimilation" in terms
    assert "ClaimGuard" in terms


def test_missing_module_marked_planned_in_outline():
    # If any optional module is absent its outline chapter is planned/missing.
    chapters = SolarisArchitectureOutlineBuilder().build()
    for c in chapters:
        assert c.to_dict()["implementation_status"] in (
            "implemented", "planned_or_missing")
