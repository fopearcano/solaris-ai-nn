"""Forbidden claims: registry loads, patterns classify, replacements exist."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import (
    ForbiddenClaimCategory,
    ForbiddenClaimRegistry,
)


def test_forbidden_registry_loads():
    r = ForbiddenClaimRegistry.build()
    assert r.patterns
    d = r.to_dict()
    assert d["pattern_count"] > 0
    assert ForbiddenClaimCategory.CONSCIOUSNESS in d["categories"]


def test_forbidden_patterns_classify():
    r = ForbiddenClaimRegistry.build()
    cats = {c.category for c in r.scan_text("Solaris is conscious. Solaris is "
                                            "alive. Solaris understands.")}
    assert ForbiddenClaimCategory.CONSCIOUSNESS in cats
    assert ForbiddenClaimCategory.BIOLOGICAL_LIFE in cats
    assert ForbiddenClaimCategory.UNDERSTANDING in cats


def test_replacement_suggestions_exist():
    r = ForbiddenClaimRegistry.build()
    for p in r.patterns:
        assert p.replacement
    for c in r.scan_text("Solaris is conscious."):
        assert c.replacement


def test_disclaimed_text_not_flagged():
    r = ForbiddenClaimRegistry.build()
    assert r.scan_text("Solaris is not conscious; it makes no claim of "
                       "consciousness.") == []
