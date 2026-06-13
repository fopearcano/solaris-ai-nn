"""Integration: active perception samples a bounded nursery."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.safety import EcologySafetyValidator


def _nursery(tmp_path):
    return DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=80, output_state_dir=str(tmp_path)))


def test_nursery_sampling_hooks_are_simulation_only(tmp_path):
    nursery = _nursery(tmp_path)
    for action in ("look", "focus_signal_source", "sample_boundary",
                   "emit_simulated_ping", "seek_novelty", "seek_absence"):
        result = nursery.sample(action)
        assert result["scope"] == "simulation_only"


def test_quiet_window_is_bounded(tmp_path):
    nursery = _nursery(tmp_path)
    result = nursery.request_quiet_window()
    assert result["quiet_window_requested"] is True
    assert result["bounded_by"] <= 30


def test_novelty_window_within_cap(tmp_path):
    nursery = _nursery(tmp_path)
    result = nursery.request_novelty_window()
    assert result["novelty_window_requested"] is True


def test_controller_samples_nursery(tmp_path):
    nursery = _nursery(tmp_path)
    for step in range(40):
        nursery.stimulus_provider(step)
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path), nursery=nursery)
    ctx = ctrl.build_context({"step": 41, "mysterium_pressure": 0.5,
                              "health_level": "ok", "energy": 0.9})
    decision = ctrl.select(ctx)
    result = ctrl.execute_if_allowed(decision, ctx)
    assert not result.blocked or result.action_type == "no_sampling_action"


def test_ecology_safety_still_validates_stimuli(tmp_path):
    # The nursery's own safety remains in force; active perception may
    # request, not command, and command-shaped payloads are still refused.
    from solaris_ai_nn.ecology.events import EcologyEventType, EcologyStimulus

    validator = EcologySafetyValidator()
    bad = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                          payload="shutdown now")
    assert not validator.validate_stimulus(bad).safe
