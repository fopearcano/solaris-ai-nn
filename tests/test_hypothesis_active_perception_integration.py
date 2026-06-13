"""Integration: hypotheses drive active-perception sampling, and back."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType


def _engine(tmp_path):
    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    return HypothesisEngine(state_dir=tmp_path,
                            active_perception=controller)


def test_hypothesis_creates_sampling_target(tmp_path):
    engine = _engine(tmp_path)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge may be weak", target_ref="node_42")
    ctx = engine.sampling_target_for(h)
    assert ctx["world_model"]["low_confidence_nodes"] == ["node_42"]


def test_sampling_result_becomes_evidence(tmp_path):
    engine = _engine(tmp_path)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge may be weak", target_ref="node_42")
    engine.memory.add(h)
    result = engine.test_via_active_perception(h)
    assert result is not None
    assert result.evidence is not None
    # The evidence was appended to the ledger.
    assert engine.runner.evidence_ledger.snapshot()["evidence_count"] >= 1


def test_proto_symbol_target_routes_to_proto(tmp_path):
    engine = _engine(tmp_path)
    h = Hypothesis(type=HypothesisType.PROTO_SYMBOL_GROUNDING,
                   statement="symbol may be ambiguous", target_ref="SIG_0001")
    ctx = engine.sampling_target_for(h)
    assert "SIG_0001" in ctx["proto_language"]["ambiguous_symbols"]
