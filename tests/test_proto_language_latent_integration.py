"""Tests for proto-language across latent replay."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer
from solaris_ai_nn.protolanguage.symbol_emergence import SymbolCandidate
from solaris_ai_nn.protolanguage.symbols import SymbolType


def test_latent_replay_uses_symbolized_traces(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5}})
    # A replayed trace window symbolizes exactly like a live one --
    # shorter, evidence-preserving, offline by labelling.
    replay_trace = [{"kind": "replayed_stimulus",
                     "pattern": "light_noise"}] * 8
    symbolized = layer.compression.symbolize_trace(replay_trace,
                                                   layer.registry)
    report = layer.compression.evaluate_compression(replay_trace,
                                                    symbolized)
    assert report["compression_ratio"] < 1.0
    assert symbolized.tokens()  # symbols usable inside replay
    # Sequences observed under offline context train prediction too.
    layer.prediction.train_counts([symbolized.tokens()])
    assert layer.prediction.trained_sequences == 1


def test_counterfactual_symbol_stays_offline(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    accepted = layer.emergence.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.LATENT_SCHEMA,
        grounding_summary="dream_schema",
        evidence_refs=["counterfactual:dream_3"],
        evidence_kind="counterfactual", offline=True,
        source_module="latent"))
    assert accepted is not None
    assert accepted.offline_born
    # Its groundings carry the counterfactual kind forever.
    kinds = {g.evidence_kind for g in accepted.grounding_refs}
    assert kinds == {"counterfactual"}
    # And the safety validator confirms it can never become real.
    accepted.metadata["offline"] = False  # a hostile mutation
    report = layer.safety.validate_symbol(accepted)
    assert not report.safe


def test_latent_scan_context_is_offline(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    candidates = layer.emergence.scan_context({
        "latent_schemas": {"rest_recovery_schema": 1},
        "offline_replay": True})
    assert candidates
    assert all(c.offline for c in candidates)
    symbols = layer.emergence.propose_symbols(candidates)
    assert all(s.offline_born for s in symbols)


def test_symbol_ambiguity_can_raise_mysterium_input(tmp_path):
    """Ambiguous symbols feed unknown pressure (via homeostasis ctx)."""
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5}})
    symbol = list(layer.registry.symbols.values())[0]
    layer.registry.mark_ambiguous(symbol.symbol_id, "scattered")
    summary = layer.summary()
    assert summary["ambiguous_symbol_count"] >= 1
