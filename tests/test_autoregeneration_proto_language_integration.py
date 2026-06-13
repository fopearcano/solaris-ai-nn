"""Integration: symbol hygiene works against a real symbol registry."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    make_repair,
)
from solaris_ai_nn.autoregeneration.repair_policy import RepairDecision
from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import ProtoSymbol, SymbolType


def _registry_with_symbol():
    registry = SymbolRegistry()
    symbol = ProtoSymbol(token="SIG_LIGHT_0001", type=SymbolType.STIMULUS)
    registry.symbols[symbol.symbol_id] = symbol
    return registry, symbol


def test_symbol_hygiene_marks_stale_in_registry(tmp_path):
    registry, symbol = _registry_with_symbol()
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"),
        symbol_registry=registry)
    decision = RepairDecision(
        action=make_repair(RepairActionType.MARK_SYMBOL_STALE,
                           target_ref=symbol.symbol_id),
        mode="safe_auto_repair", apply_allowed=True)
    result = engine._handle(decision, {"state_dir": str(tmp_path)})
    assert result.applied is True
    assert symbol.status == "stale"


def test_symbol_explosion_warning_reduced_by_marking():
    from solaris_ai_nn.autoregeneration.symbol_hygiene import (
        SymbolHygieneManager,
    )

    mgr = SymbolHygieneManager()
    actions = mgr.propose({"proto_language": {
        "symbol_count": 900, "stale_symbols": ["S1", "S2", "S3"]}})
    # Marking stale symbols is the proposed mitigation for explosion.
    assert sum(1 for a in actions
               if a.action_type == "mark_symbol_stale") >= 3
