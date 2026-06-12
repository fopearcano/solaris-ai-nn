"""Tests for semantic grounding."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.semantic_grounding import (
    GROUNDING_DIMENSIONS,
    SemanticGroundingEngine,
)
from solaris_ai_nn.protolanguage.symbols import ProtoSymbol, SymbolType


def _symbol():
    return ProtoSymbol(token="HAB_REST_0001", type=SymbolType.HABIT)


def test_symbol_grounded_in_signal_action_reaction():
    engine = SemanticGroundingEngine()
    symbol = _symbol()
    meaning = engine.ground_symbol(symbol, {
        "signal_pattern": "low_energy", "action_tendency": "rest",
        "reaction_valence": 0.6, "need_state": "restore_energy"})
    assert meaning.dimensions["signal_pattern"] == ["low_energy"]
    assert meaning.dimensions["action_tendency"] == ["rest"]
    assert meaning.dimensions["reaction_valence"] == ["0.6"]
    assert "not human understanding" in meaning.note
    # The symbol's grounding refs grew alongside.
    dims = {g.dimension for g in symbol.grounding_refs}
    assert {"signal_pattern", "action_tendency",
            "reaction_valence"} <= dims
    assert set(meaning.dimensions) <= set(GROUNDING_DIMENSIONS)


def test_ambiguity_measured():
    engine = SemanticGroundingEngine()
    consistent = _symbol()
    for _ in range(6):
        engine.ground_symbol(consistent, {"context": "quiet",
                                          "action_tendency": "rest"})
    assert engine.measure_ambiguity(consistent) < 0.2
    scattered = ProtoSymbol(token="UNK_X_0001",
                            type=SymbolType.UNKNOWN)
    for ctx in ("a", "b", "c", "d", "e"):
        engine.ground_symbol(scattered, {"context": ctx})
    assert engine.measure_ambiguity(scattered) \
        > engine.measure_ambiguity(consistent)
    assert scattered.ambiguity_score > consistent.ambiguity_score
    # Ungrounded symbols are ambiguous by default, not assumed clear.
    fresh = ProtoSymbol(token="ENT_Y_0001", type=SymbolType.ENTITY)
    assert engine.measure_ambiguity(fresh) == 0.5


def test_real_offline_evidence_distinguished():
    engine = SemanticGroundingEngine()
    symbol = _symbol()
    engine.ground_symbol(symbol, {"context": "live",
                                  "evidence_kind": "real"})
    engine.ground_symbol(symbol, {"context": "replayed",
                                  "evidence_kind": "offline"})
    engine.ground_symbol(symbol, {"context": "dreamed",
                                  "evidence_kind": "counterfactual"})
    kinds = engine.evidence_kind_summary(symbol)
    assert kinds == {"real": 1, "offline": 1, "counterfactual": 1}
    # The symbol's grounding refs carry the kinds individually.
    ref_kinds = {g.evidence_kind for g in symbol.grounding_refs}
    assert {"real", "offline", "counterfactual"} <= ref_kinds


def test_stability_rises_with_consistent_repetition():
    engine = SemanticGroundingEngine()
    symbol = _symbol()
    first = engine.ground_symbol(symbol, {"context": "quiet"})
    initial_stability = first.stability
    for _ in range(9):
        meaning = engine.ground_symbol(symbol, {"context": "quiet"})
    assert meaning.stability > initial_stability
    assert symbol.stability_score == meaning.stability
