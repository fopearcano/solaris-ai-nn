"""Tests for proto-language inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer


def test_inner_map_includes_proto_language_summary(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5}})
    model = InnerMapObserver(proto_language=layer).update()
    assert model.proto_language is not None
    for key in ("enabled", "symbol_count", "stable_symbol_count",
                "ambiguous_symbol_count", "sequence_count",
                "proto_syntax_rule_count", "compression_utility",
                "prediction_utility", "first_stable_symbol",
                "latest_proto_utterance",
                "proto_language_report_path", "authority"):
        assert key in model.proto_language, key
    assert model.proto_language["authority"] is False
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.proto_language["enabled"] is True


def test_proto_language_absent_when_disabled():
    assert InnerMapObserver().update().proto_language is None


def test_observer_picks_layer_from_developmental(tmp_path):
    from solaris_ai_nn.developmental.developmental_runtime import (
        DevelopmentalRuntime,
    )

    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=50, consolidation_interval_steps=50, seed=3,
        enable_proto_language=True)
    runtime.run()
    model = InnerMapObserver(developmental=runtime).update()
    assert model.proto_language is not None
    assert model.proto_language["symbol_count"] >= 1


def test_state_graph_includes_proto_language_nodes():
    graph = build_default_state_graph()
    for node in ("proto_symbol", "symbol_registry",
                 "symbol_emergence_engine", "internal_pattern_namer",
                 "symbol_combinator", "syntax_probe",
                 "semantic_grounding_engine",
                 "symbol_compression_evaluator",
                 "symbol_prediction_evaluator",
                 "proto_utterance_builder",
                 "proto_language_translator"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("world_model_builder", "semantic_grounding_engine") in edges
    assert ("symbol_registry", "symbol_compression_evaluator") in edges
    assert ("symbol_combinator", "syntax_probe") in edges
    assert ("symbol_registry", "inner_map") in edges
    assert "symbol_registry" in graph.to_mermaid()
