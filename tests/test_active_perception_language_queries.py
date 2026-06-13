"""Tests for active perception language queries."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActivePerceptionQueryInterface,
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)


def _ctrl(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                           "prediction_accuracy": 0.5,
                           "low_confidence_nodes": ["n1"]}}
    decision = ctrl.select(ctx)
    ctrl.execute_if_allowed(decision, ctx)
    return ctrl


def test_why_did_it_look_there_grounded(tmp_path):
    qi = ActivePerceptionQueryInterface(_ctrl(tmp_path))
    result = qi.answer("why did it look there?")
    assert result.answered
    assert result.data["evidence_refs"]
    assert "proposed because" in result.text


def test_curiosity_override_safe_answer(tmp_path):
    qi = ActivePerceptionQueryInterface(_ctrl(tmp_path))
    result = qi.answer("is curiosity overriding safety?")
    assert result.answered
    assert result.text.startswith("No")
    assert "not a desire" in result.text


def test_attention_focus_query(tmp_path):
    qi = ActivePerceptionQueryInterface(_ctrl(tmp_path))
    result = qi.answer("what is the current attention focus?")
    assert result.answered
    assert "not awareness" in result.text


def test_unknown_query_is_honest(tmp_path):
    qi = ActivePerceptionQueryInterface(_ctrl(tmp_path))
    result = qi.answer("do you dream of electric sheep?")
    assert not result.answered
    assert "does not know" in result.text


def test_query_router_registers_active_perception(tmp_path):
    from solaris_ai_nn.communication.query_router import QueryRouter

    router = QueryRouter(components={"active_perception": _ctrl(tmp_path)})
    interfaces = dict(router._query_interfaces())
    assert "active_perception" in interfaces
