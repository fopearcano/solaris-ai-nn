"""Tests for the world model fed by latent cognition."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.latent import (
    DreamCycle,
    LatentMemoryStore,
    MysteriumTracker,
)
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.nodes import NodeType


def _bridge(steps=30):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(steps):
        bridge.process(C.Stimulus(payload=f"p{i % 3}", intensity=0.5))
        bridge.react(C.Reaction(valence=1.0 if i % 2 else -0.5))
    return bridge


def test_latent_replay_updates_offline_evidence(tmp_path):
    bridge = _bridge()
    store = LatentMemoryStore(tmp_path)
    dream = DreamCycle(bridge=bridge, store=store, seed=2)
    dream.run(20)

    builder = WorldModelBuilder()
    builder.update_from_latent_report(
        {"mysterium_reasons": [], "mode": "dream"},
        dreams=store.dreams())
    schemas = builder.graph.find(node_type=NodeType.LATENT_SCHEMA)
    assert schemas
    offline_edges = [e for e in builder.graph.edges.values()
                     if e.offline_observation_count > 0]
    assert offline_edges
    # Offline evidence never counts as real observation.
    assert all(e.observation_count == 0 for e in offline_edges)
    ratio = builder.graph.evidence_ratio()
    assert ratio["offline"] > 0


def test_consolidated_schemas_enter_graph(tmp_path):
    from solaris_ai_nn.latent import ConsolidatedSchema

    builder = WorldModelBuilder()
    builder.update_from_latent_report(
        {"mode": "sleep"},
        schemas=[ConsolidatedSchema(pattern="Stimulus:2",
                                    dominant_action="approach",
                                    support_count=5)])
    schema = builder.graph.get_node(NodeType.LATENT_SCHEMA, "Stimulus:2")
    assert schema is not None
    predicts = [e for e in builder.graph.edges.values()
                if e.type == "predicts"]
    assert predicts
    assert builder.graph.nodes[predicts[0].target_node_id].label \
        == "approach"


def test_mysterium_changes_with_prediction_misses():
    mysterium = MysteriumTracker(pressure=0.3)
    builder = WorldModelBuilder(mysterium=mysterium)
    # Train the graph on one pattern...
    for _ in range(8):
        builder.update_from_reaction("approach", 1.0)
    before = mysterium.pressure
    # ...then score graph predictions against a contradicting world.
    for _ in range(5):
        prediction = builder.predictor.predict_next(
            {"action": "approach"}, builder.graph)
        builder.predictor.score_prediction(prediction, {
            "valence_bucket": "negative", "is_absence": True})
    assert mysterium.pressure > before  # misses raised unknown pressure
    # And hits drain it again.
    peak = mysterium.pressure
    for _ in range(5):
        prediction = builder.predictor.predict_next(
            {"action": "approach"}, builder.graph)
        builder.predictor.score_prediction(prediction, {
            "valence_bucket": "positive", "is_absence": False})
    assert mysterium.pressure < peak


def test_mysterium_reasons_become_unknown_nodes():
    builder = WorldModelBuilder()
    builder.update_from_latent_report({
        "mysterium_reasons": ["repeated prediction misses",
                              "replay failed to reproduce"],
        "mode": "replay"})
    unknowns = [n for n in builder.graph.find(node_type=NodeType.UNKNOWN)
                if n.metadata.get("mysterium")]
    assert len(unknowns) == 2
    summary = builder.world_model_summary()
    assert len(summary["high_mysterium_areas"]) == 2
