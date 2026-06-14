"""Sensory <-> Inner MAP: model field, observer wiring, state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

_NODES = (
    "sensory_membrane_runtime", "sensory_source_registry",
    "read_only_contract_validator", "jsonl_stream_adapter",
    "text_stream_adapter", "numeric_stream_adapter", "folder_poll_adapter",
    "sensory_event_normalizer", "sensory_buffer", "sensory_grounding_engine",
    "sensory_provenance_ledger", "sensory_membrane_safety_validator",
)


def test_model_has_sensory_membrane_field():
    assert hasattr(InnerMapModel(), "sensory_membrane")
    assert InnerMapModel().sensory_membrane is None


def test_state_graph_has_twelve_sensory_nodes():
    g = build_default_state_graph()
    for node in _NODES:
        assert node in g.nodes, node


def test_state_graph_links_membrane_to_inner_map():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("sensory_membrane_runtime", "inner_map") in edges


def test_observer_reports_membrane_summary():
    status = {"enabled": True, "source_count": 2, "active_source_count": 2,
              "read_only": True}
    model = InnerMapObserver(sensory_membrane=status).update()
    assert model.sensory_membrane is not None
    assert model.sensory_membrane["read_only"] is True
