"""Tests for symbol hygiene."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.symbol_hygiene import SymbolHygieneManager


def test_duplicate_symbols_propose_merge():
    mgr = SymbolHygieneManager()
    actions = mgr.propose({"proto_language": {
        "duplicate_symbols": ["S1|S2"]}})
    assert any(a.action_type == "merge_duplicate_symbols" for a in actions)


def test_stale_symbol_marked():
    mgr = SymbolHygieneManager()
    actions = mgr.propose({"proto_language": {"stale_symbols": ["S3"]}})
    assert any(a.action_type == "mark_symbol_stale"
               and a.target_ref == "S3" for a in actions)


def test_ungrounded_symbol_flagged():
    mgr = SymbolHygieneManager()
    actions = mgr.propose({"proto_language": {"ungrounded_symbols": ["S4"]}})
    assert any(a.target_ref == "S4" for a in actions)


def test_explosion_detected():
    mgr = SymbolHygieneManager()
    detected = mgr.detect({"proto_language": {"symbol_count": 900}})
    assert detected["explosion"] is True


def test_ambiguous_requests_disambiguation():
    mgr = SymbolHygieneManager()
    mgr.propose({"proto_language": {"ambiguous_symbols": ["S5"]}})
    assert "S5" in mgr.disambiguation_requests


def test_apply_to_registry_marks_stale():
    from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
    from solaris_ai_nn.protolanguage.symbols import ProtoSymbol, SymbolType

    registry = SymbolRegistry()
    symbol = ProtoSymbol(token="SIG_LIGHT_0001", type=SymbolType.STIMULUS)
    registry.symbols[symbol.symbol_id] = symbol
    from solaris_ai_nn.autoregeneration.repair_actions import (
        RepairActionType,
        make_repair,
    )

    mgr = SymbolHygieneManager()
    action = make_repair(RepairActionType.MARK_SYMBOL_STALE,
                         target_ref=symbol.symbol_id)
    assert mgr.apply_to_registry(registry, action) is True
