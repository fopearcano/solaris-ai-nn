"""Integration: world-model contradiction feeds LOGOS tension."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine, ResolutionPolicy
from solaris_ai_nn.logos_complexity.synthesis import SynthesisType
from solaris_ai_nn.logos_complexity.tension import TensionType


def test_contradiction_feeds_tension(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|contradicts|b"]}})
    by_type = engine.fracture.snapshot()["by_type"]
    assert by_type.get(TensionType.WORLD_MODEL_CONTRADICTION, 0) >= 1


def test_contradiction_can_spawn_hypothesis(tmp_path):
    engine = LogosComplexityEngine(
        state_dir=tmp_path,
        policy=ResolutionPolicy(mode="synthesis_preferred"))
    engine.tick({"world_model": {"contradiction_edges": ["a|contradicts|b"],
                                 "prediction_accuracy": 0.2}})
    # A contradiction proposal set includes create_hypothesis.
    from solaris_ai_nn.logos_complexity.synthesis import SynthesisEngine
    from solaris_ai_nn.logos_complexity.tension import (
        LogosTension,
        TensionPolarity,
    )

    t = LogosTension(tension_type=TensionType.WORLD_MODEL_CONTRADICTION,
                     polarity_a=TensionPolarity.SUPPORT,
                     polarity_b=TensionPolarity.CONTRADICTION,
                     evidence_refs=["e"])
    candidates = SynthesisEngine().propose(t, {})
    assert any(c.synthesis_type == SynthesisType.CREATE_HYPOTHESIS
               for c in candidates)


def test_contradiction_evidence_preserved_in_graph(tmp_path):
    from solaris_ai_nn.world_model.builder import WorldModelBuilder
    from solaris_ai_nn.world_model.edges import EdgeType
    from solaris_ai_nn.world_model.nodes import NodeType
    from solaris_ai_nn.logos_complexity.synthesis import (
        SynthesisCandidate,
        SynthesisEngine,
    )

    builder = WorldModelBuilder()
    a = builder.graph.upsert_node(NodeType.UNKNOWN, "a")
    b = builder.graph.upsert_node(NodeType.UNKNOWN, "b")
    edge = builder.graph.upsert_edge(a, EdgeType.CONTRADICTS, b,
                                    weight_delta=2.0, evidence="observed")
    engine = SynthesisEngine(world_model=builder)
    candidate = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.MARK_AMBIGUOUS,
        metadata={"edge_id": edge.edge_id})
    result = engine.apply_if_allowed(candidate, {})
    assert result.applied is True
    # Edge still present and its evidence is preserved.
    assert edge.edge_id in builder.graph.edges
    assert edge.evidence_refs
