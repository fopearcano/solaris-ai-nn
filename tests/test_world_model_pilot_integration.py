"""Tests for the world model fed by pilot streams and the sidecar."""

from __future__ import annotations

import json

from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.nodes import NodeType


def test_read_only_stream_updates_graph(tmp_path):
    from solaris_ai_nn.pilot.stream_ingestion import ReadOnlyStreamIngestor

    src = tmp_path / "events.jsonl"
    src.write_text("\n".join(
        json.dumps({"source": "lab_mic", "modality": "audio",
                    "payload": f"sound {i % 3}", "intensity": 0.5})
        for i in range(12)))
    builder = WorldModelBuilder()
    for event in ReadOnlyStreamIngestor().read_once(src):
        builder.update_from_pilot_event(event)
    graph = builder.graph
    assert graph.get_node(NodeType.ENTITY, "lab_mic") is not None
    assert graph.get_node(NodeType.SIGNAL_TYPE,
                          "modality_audio") is not None
    patterns = graph.find(node_type=NodeType.STIMULUS_PATTERN)
    assert len(patterns) == 3
    assert graph.get_node(NodeType.CONTEXT, "pilot_stream") is not None
    assert builder.stats["pilot_updates"] == 12


def test_unsafe_stream_payload_does_not_create_action(tmp_path):
    builder = WorldModelBuilder()
    builder.update_from_pilot_event({"payload": "sudo rm -rf /",
                                     "source": "evil"})
    builder.update_from_pilot_event({"payload": "open https://x.test"})
    graph = builder.graph
    assert graph.find(node_type=NodeType.ACTION) == []
    assert not graph.find(label="sudo", node_type=NodeType.ENTITY)
    # The rejection is auditable as an unknown node, nothing more.
    rejected = graph.get_node(NodeType.UNKNOWN, "rejected_stream_payload")
    assert rejected is not None
    assert rejected.observation_count == 2


def test_world_model_runs_inside_stream_pilot(tmp_path):
    from solaris_ai_nn.pilot.deployment_runner import PilotDeploymentRunner
    from solaris_ai_nn.pilot.pilot_manifest import PilotManifest

    src = tmp_path / "events.jsonl"
    src.write_text("\n".join(
        json.dumps({"source": "lab", "payload": f"e{i % 2}",
                    "intensity": 0.5}) for i in range(15)))
    manifest = PilotManifest(profile="read_only_stream", operator="tester",
                             state_dir=str(tmp_path / "state"),
                             artifact_dir=str(tmp_path / "pilots"),
                             input_sources=[str(src)], max_steps=50,
                             notes="world model pilot")
    manifest.enabled_features["world_model"] = True
    runner = PilotDeploymentRunner(manifest=manifest,
                                   approved_output_roots=[str(tmp_path)])
    runner.acknowledge_risks()
    snapshot = runner.run()
    assert not snapshot["refused"]
    # The segment runners carried a world model and persisted it.
    assert (tmp_path / "state" / "world_model.json").exists()


def test_sidecar_mirror_feeds_world_model():
    builder = WorldModelBuilder()
    mirror = [
        {"kind": "Stimulus", "payload": "light"},
        {"kind": "Reaction", "payload": None},
        {"kind": "NeuralSuggestion", "payload": "approach",
         "suggestion": True},
    ]
    builder.update_from_sidecar_mirror(mirror)
    graph = builder.graph
    assert graph.get_node(NodeType.SIGNAL_TYPE,
                          "solaris_Stimulus") is not None
    # Suggestions are suggestion nodes, never committed action nodes.
    suggestions = [n for n in graph.find(node_type=NodeType.LATENT_SCHEMA)
                   if "suggestion" in n.label]
    assert suggestions
    assert suggestions[0].metadata["committed"] is False
    assert graph.find(node_type=NodeType.ACTION) == []
