"""Allowed language: registry loads; phrases never imply consciousness/life/agency."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import AllowedOperationalLanguageRegistry


def test_allowed_language_registry_loads():
    r = AllowedOperationalLanguageRegistry.build()
    assert r.phrases
    assert r.replacements
    assert r.to_dict()["phrase_count"] > 0


def test_allowed_phrases_do_not_imply_inner_life():
    r = AllowedOperationalLanguageRegistry.build()
    assert r.all_phrases_safe() is True
    for p in r.phrases:
        assert p.implies_inner_life() is False


def test_suggest_returns_operational_replacement():
    r = AllowedOperationalLanguageRegistry.build()
    s = r.suggest("consciousness_claim")
    assert "operational" in s.lower() or "no consciousness" in s.lower()
