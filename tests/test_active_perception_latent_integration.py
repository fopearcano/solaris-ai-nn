"""Integration: latent sampling stays internal/offline."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)


def test_replay_uncertain_trace_is_internal_only(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path), latent=object())
    action = SamplingAction(
        action_type=SamplingActionType.REPLAY_UNCERTAIN_TRACE,
        scope=SamplingScope.INTERNAL_ONLY)
    from solaris_ai_nn.active_perception.sampling_policy import (
        SamplingDecision,
    )

    result = ctrl.execute_if_allowed(
        SamplingDecision(action=action, mode="balanced"), {"step": 0})
    assert result.scope == "internal_only"
    assert result.executed is True
    assert "offline" in result.detail or "internal" in result.detail


def test_replay_candidate_maps_to_latent_action():
    action = SamplingAction(
        action_type=SamplingActionType.REPLAY_UNCERTAIN_TRACE,
        scope=SamplingScope.INTERNAL_ONLY)
    candidate = action.to_action_candidate()
    assert candidate.action_type == "latent_action"
    assert candidate.executable_scope == "internal_only"


def test_counterfactual_divergence_feeds_uncertainty():
    from solaris_ai_nn.active_perception.uncertainty import (
        UncertaintyEstimator,
        UncertaintySource,
    )

    est = UncertaintyEstimator()
    state = est.estimate({"counterfactual_divergence": 0.6})
    sources = {t.source for t in state.targets}
    assert UncertaintySource.COUNTERFACTUAL_DIVERGENCE in sources
