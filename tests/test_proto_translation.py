"""Tests for the proto-language translator."""

from __future__ import annotations

import re

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import SymbolType
from solaris_ai_nn.protolanguage.translation import (
    ProtoLanguageTranslator,
)


def test_cautious_translation_generated():
    translator = ProtoLanguageTranslator()
    text = translator.translate_tokens(
        ["ABS_0001", "NEED_SIGNAL_0001", "ACT_LOOK_0001"])
    assert text.startswith("An absence pattern was followed by")
    assert "need pressure" in text
    assert "action suggestion" in text
    assert "debug translation" in text
    assert "not human language" in text
    assert translator.translations_made == 1


def test_no_new_facts():
    """Translation content is a deterministic function of the tokens."""
    translator = ProtoLanguageTranslator()
    a = translator.translate_tokens(["UNK_SPIKE_0001"])
    b = translator.translate_tokens(["UNK_SPIKE_0001"])
    assert a == b  # same tokens, same text -- nothing invented
    # The text contains no numbers that were not in the tokens.
    numbers = set(re.findall(r"\d+", a))
    assert numbers <= {"0001", "1"}
    # Unknown tokens are named as unparsed, not embellished.
    odd = translator.translate_tokens(["???"])
    assert "unparsed internal token" in odd


def test_claim_guard_scans_translation():
    translator = ProtoLanguageTranslator()
    guard = ClaimGuard()
    for tokens in (["ABS_0001"], ["HAB_REST_0001", "RCT_POS_0001"],
                   ["MILE_FIRST_0001"], ["SELF_BND_0001"]):
        text = translator.translate_tokens(tokens)
        assert guard.is_safe(text), tokens


def test_ambiguity_marked_in_translation():
    registry = SymbolRegistry()
    symbol = registry.upsert_symbol(SymbolType.UNKNOWN, "spike",
                                    evidence_refs=["u:1"])
    registry.mark_ambiguous(symbol.symbol_id, "inconsistent grounding")
    translator = ProtoLanguageTranslator(registry=registry)
    text = translator.translate_tokens([symbol.token])
    assert "[ambiguous]" in text  # uncertainty stays visible


def test_uncertainty_suffix_always_present():
    translator = ProtoLanguageTranslator()
    assert "approximate" in translator.translate_tokens(["ACT_X_0001"])
    assert "approximate" in translator.translate_tokens([])
