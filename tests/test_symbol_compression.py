"""Tests for symbol compression."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.compression import (
    SymbolCompressionEvaluator,
)
from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import SymbolType


def _registry():
    registry = SymbolRegistry()
    registry.upsert_symbol(SymbolType.STIMULUS, "light_noise",
                           evidence_refs=["sig:light_noise"])
    return registry


def test_symbolized_trace_shorter_when_repeated():
    evaluator = SymbolCompressionEvaluator()
    registry = _registry()
    trace = [{"kind": "stimulus", "pattern": "light_noise"}] * 12 \
        + [{"kind": "other", "x": 1}]
    symbolized = evaluator.symbolize_trace(trace, registry)
    report = evaluator.evaluate_compression(trace, symbolized)
    assert report["compression_ratio"] < 0.5  # run-length folded
    assert report["symbolized_trace_length"] \
        < report["raw_trace_length"]
    # Repeats are recorded, not lost.
    folded = [e for e in symbolized.entries if e.get("repeat")]
    assert folded and folded[0]["repeat"] == 12


def test_compression_preserves_evidence_refs():
    evaluator = SymbolCompressionEvaluator()
    registry = _registry()
    trace = [{"kind": "stimulus", "pattern": "light_noise"}] * 5
    symbolized = evaluator.symbolize_trace(trace, registry)
    report = evaluator.evaluate_compression(trace, symbolized)
    assert report["evidence_retained"] is True
    token_entries = [e for e in symbolized.entries if e.get("token")]
    assert all(e["evidence_ref"] for e in token_entries)
    assert "never deletes raw evidence" in report["note"]


def test_safety_incidents_not_hidden():
    evaluator = SymbolCompressionEvaluator()
    registry = _registry()
    trace = ([{"kind": "stimulus", "pattern": "light_noise"}] * 6
             + [{"kind": "boundary_violation", "detail": "blocked"}]
             + [{"kind": "emergency", "detail": "stop requested"}])
    symbolized = evaluator.symbolize_trace(trace, registry)
    report = evaluator.evaluate_compression(trace, symbolized)
    assert report["safety_events_in_raw"] == 2
    assert report["safety_events_kept_verbatim"] == 2
    assert report["safety_events_hidden"] == 0
    protected = [e for e in symbolized.entries if e.get("protected")]
    assert len(protected) == 2
    assert all(e["token"] is None for e in protected)


def test_compression_feeds_symbol_scores():
    evaluator = SymbolCompressionEvaluator()
    registry = _registry()
    trace = [{"kind": "stimulus", "pattern": "light_noise"}] * 10
    symbolized = evaluator.symbolize_trace(trace, registry)
    report = evaluator.evaluate_compression(trace, symbolized)
    evaluator.update_symbol_scores(registry, report,
                                   symbolized.tokens())
    symbol = list(registry.symbols.values())[0]
    assert symbol.compression_score > 0
