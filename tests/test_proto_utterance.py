"""Tests for proto-utterances."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import SymbolType
from solaris_ai_nn.protolanguage.utterance import (
    UTTERANCE_PURPOSES,
    ProtoUtterance,
    ProtoUtteranceBuilder,
)


def _builder():
    registry = SymbolRegistry()
    registry.upsert_symbol(SymbolType.ABSENCE, "silence",
                           evidence_refs=["a:1"])
    registry.upsert_symbol(SymbolType.NEED, "seek_signal",
                           evidence_refs=["n:1"])
    return ProtoUtteranceBuilder(registry=registry), registry


def test_proto_utterance_serializes():
    builder, registry = _builder()
    tokens = [s.token for s in registry.symbols.values()]
    utterance = builder.build(tokens, purpose="memory",
                              context={"window": 3})
    data = utterance.to_dict()
    json.dumps(data, default=str)
    for key in ("utterance_id", "symbols", "context", "grounding_refs",
                "purpose", "confidence", "human_debug_translation",
                "metadata"):
        assert key in data, key
    assert data["rendered"].startswith("[")
    assert "not human speech" in data["note"]
    assert data["grounding_refs"]  # grounded through the registry


def test_purpose_stored():
    builder, registry = _builder()
    tokens = [s.token for s in registry.symbols.values()]
    for purpose in UTTERANCE_PURPOSES:
        utterance = builder.build(tokens, purpose=purpose)
        assert utterance.purpose == purpose
    with pytest.raises(ValueError, match="unknown utterance purpose"):
        ProtoUtterance(symbols=["ABS_0001"], purpose="poetry")
    with pytest.raises(KeyError, match="unknown symbol token"):
        builder.build(["GHOST_0001"])


def test_debug_translation_optional_and_guarded():
    builder, registry = _builder()
    tokens = [s.token for s in registry.symbols.values()]
    utterance = builder.build(tokens)
    assert utterance.human_debug_translation is None  # optional
    # First-person claims are structurally refused in translations.
    with pytest.raises(ValueError, match="first-person"):
        ProtoUtterance(symbols=["ABS_0001"],
                       human_debug_translation="I want to look around")
    safe = ProtoUtterance(
        symbols=["ABS_0001"],
        human_debug_translation="An absence pattern was recorded "
                                "(debug translation).")
    assert safe.human_debug_translation
