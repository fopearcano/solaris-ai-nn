"""Tests for the WorldModelBuilder."""

from __future__ import annotations

import json

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.nodes import NodeType


def _fed_builder(steps=30):
    builder = WorldModelBuilder()
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(steps):
        stim = C.Stimulus(payload=f"p{i % 3}", intensity=0.5,
                          is_absence=(i % 7 == 0))
        result = bridge.process(stim)
        builder.update_from_signal(stim, result)
        if i % 2 == 0:
            bridge.react(C.Reaction(valence=1.0))
            builder.update_from_reaction(result["suggested_action"], 1.0)
    return builder, bridge


def test_updates_from_signal():
    builder, _ = _fed_builder()
    assert builder.stats["signal_updates"] == 30
    assert builder.graph.get_node(NodeType.SIGNAL_TYPE,
                                  "Stimulus") is not None
    assert builder.graph.get_node(NodeType.STIMULUS_PATTERN,
                                  "absence") is not None
    assert len(builder.associations.associations) > 0


def test_updates_from_trace():
    builder, bridge = _fed_builder()
    observed = builder.update_from_trace(bridge.trace)
    assert observed > 0
    assert builder.stats["trace_updates"] == 1
    assert builder.causal.top_candidates(1)
    # The causal candidates landed in the graph as causes_candidate edges.
    assert any(e.type == "causes_candidate"
               for e in builder.graph.edges.values())


def test_updates_from_meaning_and_latent():
    from solaris_ai_nn.language.meaning_trace import atom

    builder = WorldModelBuilder()
    builder.update_from_meaning_trace([
        atom("habit", "light->approach", "reinforced", 0.8)])
    assert builder.stats["meaning_updates"] == 1
    builder.update_from_latent_report(
        {"mysterium_reasons": ["novelty"], "mode": "dream"},
        dreams=[{"dream_id": "d1", "counterfactual_kind": "invert_valence",
                 "divergence": {"score": 0.5}}])
    assert builder.stats["latent_updates"] == 1
    assert builder.graph.find(node_type=NodeType.LATENT_SCHEMA)


def test_snapshot_valid():
    builder, bridge = _fed_builder()
    builder.update_from_trace(bridge.trace)
    snap = builder.snapshot()
    json.dumps(snap, default=str)
    for key in ("node_count", "edge_count", "node_counts_by_type",
                "edge_counts_by_type", "evidence_ratio", "stats",
                "associations", "causal", "context", "predictor",
                "pruner", "safety"):
        assert key in snap, key
    assert snap["node_count"] > 1

    summary = builder.world_model_summary()
    for key in ("enabled", "graph_node_count", "graph_edge_count",
                "strongest_association", "top_causal_candidate",
                "unknown_node_count", "high_mysterium_areas",
                "context_state", "prediction_accuracy",
                "last_pruning_proposal", "evidence_ratio"):
        assert key in summary, key


def test_report_generated(tmp_path):
    builder, bridge = _fed_builder()
    builder.update_from_trace(bridge.trace)
    report = builder.to_report()
    md = report.to_markdown()
    assert "World model report" in md
    assert "Limitations and Unknowns" in md
    assert "causes_candidate" in md or "candidate" in md.lower()


def test_self_node_exists():
    builder = WorldModelBuilder()
    node = builder.graph.get_node(NodeType.SELF_REFERENCE, "solaris_ai_nn")
    assert node is not None
    assert "not identity claims" in node.metadata["note"]
