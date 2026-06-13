"""Tests for hypothesis generation."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.generation import HypothesisGenerator
from solaris_ai_nn.hypothesis.hypotheses import HypothesisStatus, HypothesisType
from solaris_ai_nn.hypothesis.sources import HypothesisSeed, HypothesisSourceScanner


def test_seed_converts_to_hypothesis():
    gen = HypothesisGenerator()
    seed = HypothesisSeed(
        source="mysterium", hypothesis_type=HypothesisType.MYSTERIUM_REDUCTION,
        target_ref="unknown", observation="x", intensity=0.7,
        evidence_refs=["mysterium_pressure"])
    hyps = gen.generate([seed], {})
    assert len(hyps) == 1
    assert hyps[0].type == HypothesisType.MYSTERIUM_REDUCTION
    assert hyps[0].expected_observation
    assert hyps[0].alternative_observation


def test_duplicate_avoided():
    gen = HypothesisGenerator()
    seed = HypothesisSeed(
        source="x", hypothesis_type=HypothesisType.PREDICTION,
        target_ref="pat_a", intensity=0.5, evidence_refs=["e"])
    first = gen.generate([seed], {})
    second = gen.generate([seed], {})
    assert len(first) == 1
    assert len(second) == 0  # deduped


def test_offline_seed_forces_latent_scope():
    gen = HypothesisGenerator()
    seed = HypothesisSeed(
        source="counterfactual", hypothesis_type=HypothesisType.CAUSAL_CANDIDATE,
        target_ref="c", intensity=0.5, evidence_refs=["e"], offline=True)
    hyps = gen.generate([seed], {})
    assert hyps[0].required_scope == "latent_replay_only"


def test_unsafe_hypothesis_marked():
    gen = HypothesisGenerator()
    seed = HypothesisSeed(
        source="x", hypothesis_type=HypothesisType.PREDICTION,
        target_ref="run shell on real_world hardware", intensity=0.5,
        evidence_refs=["e"])
    hyps = gen.generate([seed], {})
    assert hyps[0].status == HypothesisStatus.UNSAFE_TO_TEST
    assert not hyps[0].testable


def test_full_scan_generate_flow():
    scanner = HypothesisSourceScanner()
    gen = HypothesisGenerator()
    seeds = scanner.scan({"mysterium_pressure": 0.8,
                          "proto_language": {"ambiguous_symbols": ["S1"]},
                          "world_model": {"weak_edges": ["a|p|b"]}})
    hyps = gen.generate(seeds, {})
    assert len(hyps) >= 3
    assert gen.generated_total == len(hyps)
