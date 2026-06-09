"""Tests for the Inner MAP data model and JSON serialization."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import (
    BoundaryState,
    ContinuityState,
    InnerMapModel,
    MemoryState,
    ModuleState,
    NeuralSubstrateState,
    PlasticityState,
    TendencyState,
)
from solaris_ai_nn.inner_map.serialization import (
    inner_map_from_json,
    inner_map_to_json,
    load_inner_map,
    save_inner_map,
)


def _model() -> InnerMapModel:
    return InnerMapModel(
        run_id="r1",
        session_id="s1",
        continuity=ContinuityState(lifetime_steps=42, restart_count=2, alive=True),
        neural=NeuralSubstrateState(reservoir_size=64, reservoir_state_norm=3.5),
        memory=MemoryState(trace_length=10, dominant_recent_signal_type="Stimulus"),
        plasticity=PlasticityState(habit_pathways=3, pruning_count=1),
        boundaries=BoundaryState(max_steps=100, action_authority_suggest_only=True),
        tendencies=TendencyState(suggested_action="approach"),
        modules=[ModuleState("reservoir", "ESN")],
    )


def test_model_has_all_sections():
    m = _model()
    d = m.to_dict()
    for section in ("continuity", "neural", "memory", "plasticity", "boundaries",
                    "tendencies", "unknown", "modules"):
        assert section in d
    # Identity (section A).
    assert d["system_name"] == "solaris-ai-nn"
    assert d["run_id"] == "r1"
    # Runtime continuity (B), neural (C), habit/synthesis (E/F), boundaries (G).
    assert d["continuity"]["lifetime_steps"] == 42
    assert d["neural"]["reservoir_size"] == 64
    assert d["plasticity"]["habit_pathways"] == 3
    assert d["plasticity"]["pruning_count"] == 1
    assert d["boundaries"]["action_authority_suggest_only"] is True


def test_json_roundtrip_string():
    m = _model()
    text = inner_map_to_json(m)
    back = inner_map_from_json(text)
    assert isinstance(back, InnerMapModel)
    assert back.continuity.lifetime_steps == 42
    assert back.neural.reservoir_size == 64
    assert back.modules[0].name == "reservoir"


def test_from_dict_rebuilds_nested_dataclasses():
    m = _model()
    back = InnerMapModel.from_dict(m.to_dict())
    assert isinstance(back.continuity, ContinuityState)
    assert isinstance(back.neural, NeuralSubstrateState)
    assert isinstance(back.modules[0], ModuleState)


def test_save_and_load_file(tmp_path):
    m = _model()
    path = tmp_path / "inner_map.json"
    save_inner_map(m, path)
    assert path.exists()
    loaded = load_inner_map(path)
    assert loaded.run_id == "r1"
    assert loaded.tendencies.suggested_action == "approach"
