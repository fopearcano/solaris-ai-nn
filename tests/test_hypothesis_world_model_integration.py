"""Integration: supported/falsified hypotheses update world-model edges."""

from __future__ import annotations

from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType
from solaris_ai_nn.world_model.builder import WorldModelBuilder


def test_supported_hypothesis_strengthens_edge(tmp_path):
    builder = WorldModelBuilder()
    engine = HypothesisEngine(state_dir=tmp_path, world_model=builder,
                              enable_world_model_updates=True)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge may strengthen", target_ref="node_w",
                   confidence=0.7)
    nodes_before = len(builder.graph.nodes)
    engine._strengthen_world_model(h)
    assert len(builder.graph.nodes) > nodes_before
    # A predicts edge was added/strengthened from the hypothesis.
    predicts = [e for e in builder.graph.edges.values()
                if e.type == "predicts"]
    assert predicts


def test_falsified_hypothesis_adds_contradiction(tmp_path):
    builder = WorldModelBuilder()
    engine = HypothesisEngine(state_dir=tmp_path, world_model=builder,
                              enable_world_model_updates=True)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge is false", target_ref="node_f")
    engine.weaken_world_model(h)
    contradicts = [e for e in builder.graph.edges.values()
                   if e.type == "contradicts"]
    assert contradicts


def test_offline_support_does_not_promote(tmp_path):
    builder = WorldModelBuilder()
    engine = HypothesisEngine(state_dir=tmp_path, world_model=builder,
                              enable_world_model_updates=True)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge", target_ref="node_o", confidence=0.7)
    from solaris_ai_nn.hypothesis.test_runner import HypothesisTestResult

    offline_result = HypothesisTestResult(
        design_id="d", hypothesis_id=h.hypothesis_id, scope="latent_replay",
        verdict="supported", evidence={"is_offline": True})
    nodes_before = len(builder.graph.nodes)
    engine._maybe_promote(h, offline_result)
    # Offline support must not write into the world model.
    assert len(builder.graph.nodes) == nodes_before
