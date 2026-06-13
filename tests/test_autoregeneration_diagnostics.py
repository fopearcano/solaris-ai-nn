"""Tests for auto-regeneration diagnostics."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.degradation import DegradationType
from solaris_ai_nn.autoregeneration.diagnostics import (
    AutoRegenerationDiagnostics,
)


def test_scan_returns_state():
    diag = AutoRegenerationDiagnostics()
    state = diag.scan({"memory": {"over_budget": ["hot"]},
                       "mysterium_pressure": 0.97})
    types = state.counts_by_type()
    assert DegradationType.MEMORY_BLOAT in types
    assert DegradationType.MYSTERIUM_SATURATION in types


def test_partial_scan_supported():
    diag = AutoRegenerationDiagnostics()
    signals = diag.scan_symbols({"proto_language": {"symbol_count": 900}})
    assert any(s.type == DegradationType.SYMBOL_EXPLOSION for s in signals)


def test_corrupted_optional_input_does_not_crash():
    diag = AutoRegenerationDiagnostics()
    # Garbage / wrong-typed optional fields must not raise.
    state = diag.scan({"world_model": "not a dict", "memory": None,
                       "proto_language": 123})
    assert state is not None


def test_empty_context_no_signals():
    diag = AutoRegenerationDiagnostics()
    state = diag.scan({})
    assert state.signals == []


def test_diagnostics_do_not_mutate_context():
    diag = AutoRegenerationDiagnostics()
    ctx = {"memory": {"over_budget": ["hot"]},
           "proto_language": {"symbol_count": 900}}
    import copy
    before = copy.deepcopy(ctx)
    diag.scan(ctx)
    assert ctx == before


def test_world_model_contradiction_detected():
    diag = AutoRegenerationDiagnostics()
    state = diag.scan({"world_model": {
        "contradiction_edges": ["a|contradicts|b"]}})
    assert any(s.type == DegradationType.WORLD_MODEL_CONTRADICTION
               for s in state.signals)


def test_snapshot_shape():
    diag = AutoRegenerationDiagnostics()
    diag.scan({"memory": {"over_budget": ["hot"]}})
    snap = diag.snapshot()
    assert snap["scans_run"] == 1
    assert snap["last_state"] is not None
