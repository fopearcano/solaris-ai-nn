"""Whitepaper builder: generated, non-claims included, safety boundaries included."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    ArchitectureBookSafetyValidator,
    TechnicalWhitepaperBuilder,
)


def test_whitepaper_generated():
    wp = TechnicalWhitepaperBuilder().build_whitepaper()
    assert "Technical Whitepaper" in wp
    assert "## 1. Abstract" in wp
    assert "## 17. Appendix: Module Index" in wp


def test_non_claims_included():
    wp = TechnicalWhitepaperBuilder().build_whitepaper().lower()
    assert "does not prove consciousness" in wp
    assert "does not prove sentience" in wp
    assert "does not prove biological life" in wp
    assert "fixture-only by default" in wp
    assert "local-only by default" in wp


def test_safety_boundaries_included():
    wp = TechnicalWhitepaperBuilder().build_whitepaper().lower()
    assert "safety and governance" in wp
    assert "no network" in wp or "local-only" in wp


def test_overview_meets_length_target():
    ov = TechnicalWhitepaperBuilder().build_overview()
    # Target 1,500-3,000 words.
    assert 1500 <= len(ov.split()) <= 3000


def test_whitepaper_and_overview_claim_safe():
    builder = TechnicalWhitepaperBuilder()
    v = ArchitectureBookSafetyValidator()
    assert v.validate_doc_text(builder.build_whitepaper()).safe is True
    assert v.validate_doc_text(builder.build_overview()).safe is True
