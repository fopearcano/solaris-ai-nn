"""Tests for symbol memory."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.protolanguage.symbol_memory import (
    SymbolMemory,
    SymbolMemoryRecord,
)


def test_symbol_birth_recorded(tmp_path):
    memory = SymbolMemory(state_dir=tmp_path)
    memory.record("birth", token="ABS_0001", symbol_id="abc",
                  detail="recurring absence state", lifetime_s=100.0)
    path = tmp_path / "symbol_memory.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows[0]["event"] == "birth"
    assert rows[0]["token"] == "ABS_0001"
    assert rows[0]["lifetime_s"] == 100.0


def test_decay_extinction_recorded(tmp_path):
    memory = SymbolMemory(state_dir=tmp_path)
    memory.record("decay", token="CTX_OLD_0001",
                  detail="not observed for 30 windows")
    memory.record("extinction", token="CTX_OLD_0001",
                  detail="grounding stopped recurring")
    counts = memory.counts_by_event()
    assert counts["decay"] == 1
    assert counts["extinction"] == 1
    with pytest.raises(ValueError, match="unknown symbol event"):
        SymbolMemoryRecord(event="resurrection")


def test_fossilization_and_rules_recorded(tmp_path):
    memory = SymbolMemory(state_dir=tmp_path)
    memory.record("fossilization", token="MILE_FIRST_0001",
                  detail="first proto-symbol fossilized")
    memory.record("rule_emergence",
                  detail="stimulus_symbol>need_symbol>action_symbol")
    memory.record("rule_failure", detail="rule failed heldout trace")

    class FakeRule:
        def to_dict(self):
            return {"pattern": ["a", "b"], "confidence": 0.5}

    rules_path = memory.save_rules([FakeRule()])
    assert rules_path.endswith("symbol_rules.json")
    saved = json.loads((tmp_path / "symbol_rules.json").read_text())
    assert saved[0]["confidence"] == 0.5
    memory.record_sequence({"tokens": ["a", "b"], "count": 3})
    assert (tmp_path / "symbol_sequences.jsonl").exists()
    snapshot = memory.snapshot()
    assert snapshot["counts_by_event"]["fossilization"] == 1
    assert snapshot["rows_written"] == 3
