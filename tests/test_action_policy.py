"""ActionPolicyEngine: prefers useful action; avoids no-effect; no external auth."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionPolicyEngine,
    EffectLearningEngine,
    PolicyOutput,
)


def test_policy_prefers_useful_action():
    effects = EffectLearningEngine()
    for _ in range(3):
        effects.observe("shift_attention", "uncertainty_reduced",
                        "constructive")
    engine = ActionPolicyEngine()
    engine.update_from_effects(effects)
    assert engine.policy.preferences.get("shift_attention") == \
        PolicyOutput.PREFER


def test_policy_avoids_repeated_no_effect_action():
    effects = EffectLearningEngine()
    for _ in range(3):
        effects.observe("run_bounded_simulation", "no_effect", "neutral")
    engine = ActionPolicyEngine()
    engine.update_from_effects(effects)
    assert engine.policy.preferences.get("run_bounded_simulation") == \
        PolicyOutput.AVOID


def test_cannot_authorize_external_action():
    engine = ActionPolicyEngine()
    engine.update_from_effects(EffectLearningEngine())
    # Forbidden external is always blocked, regardless of evidence.
    assert engine.policy.preferences.get("forbidden_external") == \
        PolicyOutput.ALWAYS_BLOCK_FORBIDDEN
    assert "cannot authorize external action" in \
        engine.updates[0].to_dict()["note"] if engine.updates else True


def test_policy_is_internal_only():
    engine = ActionPolicyEngine()
    assert "forbidden external is always blocked" in \
        engine.policy.to_dict()["note"]
