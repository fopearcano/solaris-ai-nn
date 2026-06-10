"""Tests for the controlled vocabulary."""

from __future__ import annotations

from solaris_ai_nn.language.vocabulary import (
    CATEGORIES,
    PREDICATES,
    is_controlled,
    normalize_category,
    normalize_predicate,
)


def test_required_categories_exist():
    for cat in ("signal", "substrate", "readout", "habit", "synthesis",
                "plasticity", "memory", "inner_map", "embodiment",
                "integration", "safety", "continuity", "unknown"):
        assert cat in CATEGORIES


def test_required_predicates_exist():
    for pred in ("received", "encoded_as", "updated", "suggested",
                 "reinforced", "pruned", "blocked", "persisted", "restored",
                 "drifted", "stabilized", "explored", "failed", "succeeded",
                 "caused", "influenced"):
        assert pred in PREDICATES


def test_invalid_category_falls_back_safely():
    assert normalize_category("quantum_soul") == "unknown"
    assert normalize_category("SIGNAL") == "signal"  # case-normalised


def test_invalid_predicate_falls_back_to_hedged():
    assert normalize_predicate("manifested") == "influenced"
    assert normalize_predicate("RECEIVED") == "received"


def test_is_controlled():
    assert is_controlled("signal", "received")
    assert not is_controlled("aura", "received")
    assert not is_controlled("signal", "wanted")
