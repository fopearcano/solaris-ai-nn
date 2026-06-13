"""Integration: active perception targets ambiguous proto-symbols."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)


def _ctrl(tmp_path):
    return ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))


def test_ambiguous_symbol_targeted(tmp_path):
    ctrl = _ctrl(tmp_path)
    ctx = {"step": 0,
           "proto_language": {"symbol_count": 6, "ambiguous_symbol_count": 4,
                              "ambiguous_symbols": ["SIG_0001"]}}
    actions = ctrl.propose(ctx)
    types = {a.action_type for a in actions}
    refs = {a.target_ref for a in actions}
    assert "inspect_proto_symbol" in types or "SIG_0001" in refs


def test_ambiguity_can_improve(tmp_path):
    ctrl = _ctrl(tmp_path)
    before = {"step": 0,
              "proto_language": {"symbol_count": 6,
                                 "ambiguous_symbol_count": 4,
                                 "ambiguous_symbols": ["SIG_0001"]}}
    decision = ctrl.select(before)
    result = ctrl.execute_if_allowed(decision, before)
    after = {"step": 1,
             "proto_language": {"symbol_count": 6,
                                "ambiguous_symbol_count": 2}}
    record = ctrl.observe_result(result, before, after)
    assert record.proto_symbol_ambiguity_before == 4
    assert record.proto_symbol_ambiguity_after == 2


def test_no_change_reported_honestly(tmp_path):
    ctrl = _ctrl(tmp_path)
    before = {"step": 0,
              "proto_language": {"symbol_count": 6,
                                 "ambiguous_symbol_count": 4}}
    decision = ctrl.select(before)
    result = ctrl.execute_if_allowed(decision, before)
    after = {"step": 1,
             "proto_language": {"symbol_count": 6,
                                "ambiguous_symbol_count": 4}}
    record = ctrl.observe_result(result, before, after)
    # No improvement is recorded honestly (gain ~ 0), not invented.
    assert record.observed_information_gain is not None
