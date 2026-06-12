"""Tests for the symbol emergence engine."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.symbol_emergence import (
    SymbolCandidate,
    SymbolEmergenceEngine,
)
from solaris_ai_nn.protolanguage.symbol_registry import SymbolRegistry
from solaris_ai_nn.protolanguage.symbols import SymbolType


def _engine():
    return SymbolEmergenceEngine(registry=SymbolRegistry(),
                                 min_repetition=3)


def test_repeated_pattern_creates_candidate():
    engine = _engine()
    candidates = engine.scan_context({
        "repeated_stimulus_patterns": {"light_noise": 5, "one_off": 1},
        "absence_states": {"silence": 3},
        "boundary_events": {"pilot_input": 4}})
    summaries = {c.grounding_summary for c in candidates}
    assert "light_noise" in summaries
    assert "silence" in summaries
    assert "pilot_input" in summaries
    assert "one_off" not in summaries  # below threshold
    accepted = engine.propose_symbols(candidates)
    assert len(accepted) == 3
    assert engine.candidates_accepted == 3


def test_evidence_refs_required():
    engine = _engine()
    candidates = engine.scan_context({
        "mysterium_spikes": {"prediction_miss": 4}})
    assert all(c.evidence_refs for c in candidates)
    rejected = engine.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN, grounding_summary="x",
        evidence_refs=[]))
    assert rejected is None
    assert engine.candidates_rejected == 1
    assert "no evidence" in engine.rejections[-1]["reason"]


def test_counterfactual_symbol_marked_offline():
    engine = _engine()
    # Unmarked counterfactual: rejected.
    rejected = engine.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN,
        grounding_summary="dream_spike",
        evidence_refs=["counterfactual:dream"],
        evidence_kind="counterfactual", offline=False))
    assert rejected is None
    assert "offline" in engine.rejections[-1]["reason"]
    # Marked offline: accepted, and the symbol carries the flag.
    accepted = engine.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN,
        grounding_summary="dream_spike",
        evidence_refs=["counterfactual:dream"],
        evidence_kind="counterfactual", offline=True))
    assert accepted is not None
    assert accepted.offline_born
    # Latent-sourced scans are offline automatically.
    candidates = engine.scan_context({
        "latent_schemas": {"replay_schema": 1}})
    assert all(c.offline for c in candidates)


def test_milestones_are_singular():
    engine = _engine()
    candidates = engine.scan_context({
        "milestones": ["first_stable_habit"]})
    assert len(candidates) == 1
    assert candidates[0].symbol_type == SymbolType.MILESTONE
    symbol = engine.accept_symbol(candidates[0])
    assert symbol.token.startswith("MILE_")
