"""Integration: curiosity -> need pressure; executive inhibits unsafe
sampling."""

from __future__ import annotations

from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_curiosity_becomes_need_pressure(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    result = regulator.update({"active_perception": {
        "curiosity_pressure": 0.8, "stagnation_pressure": 0.5}})
    assert regulator.state.value("unknown_pressure", 0.0) >= 0.8
    types = {n.type for n in result.need_state.needs}
    assert "reduce_uncertainty" in types


def test_overload_becomes_fatigue(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"active_perception": {"overload_pressure": 0.8}})
    assert regulator.state.value("fatigue", 0.0) >= 0.8


def test_executive_inhibits_unsafe_sampling():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    # A sampling action with no energy should be inhibited by the resource
    # family when it carries a cost.
    action = SamplingAction(action_type=SamplingActionType.SEEK_NOVELTY,
                            scope=SamplingScope.SIMULATION_ONLY,
                            expected_cost=0.6)
    candidate = action.to_action_candidate()
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"energy": 0.05})
    assert result.inhibited is True
    assert result.reason


def test_safe_sampling_candidate_not_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    action = SamplingAction(action_type=SamplingActionType.WAIT,
                            scope=SamplingScope.INTERNAL_ONLY,
                            expected_cost=0.0)
    candidate = action.to_action_candidate()
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"energy": 0.9})
    assert result.inhibited is False
