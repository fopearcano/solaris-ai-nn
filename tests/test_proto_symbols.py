"""Tests for proto-symbols."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.protolanguage.symbols import (
    ProtoSymbol,
    SymbolConfidence,
    SymbolGrounding,
    SymbolType,
)


def test_proto_symbol_serializes():
    symbol = ProtoSymbol(token="ABS_0001", type=SymbolType.ABSENCE)
    symbol.observe("absence_states:silence", dimension="signal_pattern")
    data = symbol.to_dict()
    json.dumps(data, default=str)
    for key in ("symbol_id", "token", "type", "created_at",
                "updated_at", "grounding_refs", "observation_count",
                "compression_score", "prediction_score",
                "stability_score", "ambiguity_score", "confidence",
                "source_modules", "metadata"):
        assert key in data, key
    assert data["observation_count"] == 1
    assert "not human language" in data["note"]


def test_generated_token_not_human_language_primary():
    for token in ("S_ABS_001", "HAB_LOOP_0004", "UNK_SPIKE_0002",
                  "BND_SIDE_0001", "NEED_REST_0003"):
        ProtoSymbol(token=token, type=SymbolType.HABIT)  # accepted
    for bad in ("rest", "the_silence", "Absence", "look around"):
        with pytest.raises(ValueError, match="generated form"):
            ProtoSymbol(token=bad, type=SymbolType.HABIT)
    with pytest.raises(ValueError, match="unknown symbol type"):
        ProtoSymbol(token="ABS_0001", type="word_symbol")


def test_confidence_fields_exist():
    confidence = SymbolConfidence(compression=0.6, prediction=0.4,
                                  stability=0.8, ambiguity=0.2)
    combined = confidence.combined()
    assert 0 < combined < 0.95 or combined == 0.95
    data = confidence.to_dict()
    for key in ("compression", "prediction", "stability", "ambiguity",
                "combined"):
        assert key in data
    # Ambiguity drags confidence down; nothing reaches certainty.
    ambiguous = SymbolConfidence(compression=1.0, prediction=1.0,
                                 stability=1.0, ambiguity=1.0)
    assert ambiguous.combined() < confidence.combined()
    assert SymbolConfidence(compression=1.0, stability=1.0).combined() \
        <= 0.95


def test_stability_and_grounding():
    symbol = ProtoSymbol(token="HAB_REST_0001", type=SymbolType.HABIT)
    assert not symbol.stable
    for _ in range(6):
        symbol.observe("loop:rest", dimension="action_tendency")
    symbol.stability_score = 0.8
    symbol.ambiguity_score = 0.1
    assert symbol.stable
    with pytest.raises(ValueError, match="evidence kind"):
        SymbolGrounding(dimension="context", reference="x",
                        evidence_kind="imaginary")
    assert len(SymbolType.ALL) == 14
