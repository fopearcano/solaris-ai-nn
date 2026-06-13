"""Tests for hypothesis source scanning."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.hypotheses import HypothesisType
from solaris_ai_nn.hypothesis.sources import HypothesisSourceScanner


def test_high_mysterium_creates_seed():
    scanner = HypothesisSourceScanner()
    seeds = scanner.scan({"mysterium_pressure": 0.8})
    types = {s.hypothesis_type for s in seeds}
    assert HypothesisType.MYSTERIUM_REDUCTION in types


def test_weak_world_edge_creates_seed():
    scanner = HypothesisSourceScanner()
    seeds = scanner.scan({"world_model": {"weak_edges": ["a|predicts|b"]}})
    types = {s.hypothesis_type for s in seeds}
    assert HypothesisType.WORLD_MODEL_EDGE in types


def test_ambiguous_symbol_creates_seed():
    scanner = HypothesisSourceScanner()
    seeds = scanner.scan({"proto_language": {
        "ambiguous_symbols": ["ABS_0003"]}})
    types = {s.hypothesis_type for s in seeds}
    assert HypothesisType.PROTO_SYMBOL_GROUNDING in types


def test_delayed_group_creates_seed():
    scanner = HypothesisSourceScanner()
    seeds = scanner.scan({"ecology": {"delayed_groups": ["DLY_0001"]}})
    types = {s.hypothesis_type for s in seeds}
    assert HypothesisType.DELAYED_CONSEQUENCE in types


def test_evidence_refs_required():
    scanner = HypothesisSourceScanner()
    seeds = scanner.scan({"mysterium_pressure": 0.8,
                          "world_model": {"weak_edges": ["a|p|b"]}})
    assert seeds
    assert all(s.evidence_refs for s in seeds)


def test_empty_context_no_seeds():
    scanner = HypothesisSourceScanner()
    assert scanner.scan({}) == []


def test_rank_seeds_deterministic():
    scanner = HypothesisSourceScanner()
    ctx = {"mysterium_pressure": 0.9, "prediction_error": 0.3,
           "proto_language": {"ambiguous_symbols": ["S1"]}}
    a = [s.hypothesis_type for s in scanner.rank_seeds(scanner.scan(ctx))]
    b = [s.hypothesis_type for s in scanner.rank_seeds(scanner.scan(ctx))]
    assert a == b
