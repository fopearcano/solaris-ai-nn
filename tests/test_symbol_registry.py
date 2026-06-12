"""Tests for the symbol registry."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import SymbolType


def test_create_update_symbol(tmp_path):
    registry = SymbolRegistry(state_dir=tmp_path)
    symbol = registry.upsert_symbol(
        SymbolType.ABSENCE, "silence_window",
        evidence_refs=["absence:silence_window"],
        source_module="meaning_trace")
    assert symbol.token.startswith("ABS_")
    assert symbol.observation_count == 1
    # Same grounding -> same symbol, reinforced.
    again = registry.upsert_symbol(
        SymbolType.ABSENCE, "silence_window",
        evidence_refs=["absence:silence_window_2"])
    assert again.symbol_id == symbol.symbol_id
    assert again.observation_count == 2
    assert registry.find_by_token(symbol.token) is symbol
    assert registry.find_by_type(SymbolType.ABSENCE) == [symbol]
    assert registry.find_by_grounding("silence_window")
    with pytest.raises(ValueError, match="evidence"):
        registry.upsert_symbol(SymbolType.HABIT, "x", evidence_refs=[])


def test_merge_symbols(tmp_path):
    registry = SymbolRegistry(state_dir=tmp_path)
    a = registry.upsert_symbol(SymbolType.HABIT, "rest_loop",
                               evidence_refs=["h:1"])
    b = registry.upsert_symbol(SymbolType.HABIT, "rest_cycle",
                               evidence_refs=["h:2", "h:3"])
    kept = registry.merge_symbols(a, b, reason="same grounding shape")
    assert kept is a  # the older symbol absorbs
    assert a.observation_count == 3
    assert b.status == "merged"
    assert b.metadata["merged_into"] == a.token
    assert registry.merges[-1]["reason"] == "same grounding shape"


def test_mark_ambiguous_and_stale(tmp_path):
    registry = SymbolRegistry(state_dir=tmp_path)
    symbol = registry.upsert_symbol(SymbolType.UNKNOWN, "spike",
                                    evidence_refs=["u:1"])
    registry.mark_ambiguous(symbol.symbol_id,
                            "grounded in inconsistent contexts")
    assert symbol.status == "ambiguous"
    assert symbol.ambiguity_score >= 0.7
    assert symbol in registry.ambiguous()
    other = registry.upsert_symbol(SymbolType.CONTEXT, "old_ctx",
                                   evidence_refs=["c:1"])
    registry.mark_stale(other.symbol_id, "not observed for a long run")
    assert other.status == "stale"
    assert other not in registry.active()


def test_snapshot_and_persistence(tmp_path):
    registry = SymbolRegistry(state_dir=tmp_path)
    registry.upsert_symbol(SymbolType.NEED, "restore_energy",
                           evidence_refs=["n:1"])
    snapshot = registry.snapshot()
    assert snapshot["symbol_count"] == 1
    assert snapshot["by_type"][SymbolType.NEED] == 1
    assert "never authority" in snapshot["note"]
    registry.save()
    assert (tmp_path / "proto_symbols.json").exists()
    assert (tmp_path / "proto_symbols.jsonl").exists()
    rows = [json.loads(line) for line in
            (tmp_path / "proto_symbols.jsonl").read_text().splitlines()]
    assert rows[0]["event"] == "birth"
