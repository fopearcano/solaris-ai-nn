"""Integration: ego scope classification, governance gating, ops status."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.experiment_design import (
    ExperimentScope,
    design_for,
)
from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisType,
)


def test_scope_classified_correctly():
    # Internal hypotheses map to internal/offline experiment scopes; nursery
    # to simulation; never real-world.
    internal = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE, statement="s",
                          target_ref="e",
                          required_scope=HypothesisScope.INTERNAL_ONLY)
    nursery = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                         target_ref="p",
                         required_scope=HypothesisScope.NURSERY_ONLY)
    assert design_for(internal).scope == ExperimentScope.INTERNAL_TRACE_ANALYSIS
    assert design_for(nursery).scope == ExperimentScope.NURSERY_SIMULATION
    for h in (internal, nursery):
        assert "real_world" not in design_for(h).scope


def test_governance_gates_world_model_updates():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["hypothesis_engine"] = True
    features["hypothesis_world_model_updates"] = True
    manifest = ExperimentManifest(
        name="h", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"hypothesis_world_model_updates": True})
    assert not decision.allowed
    assert any("world-model" in r for r in decision.reasons)


def test_governance_blocks_real_world_experiment():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["hypothesis_engine"] = True
    manifest = ExperimentManifest(
        name="h", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"hypothesis_real_world": True})
    assert not decision.allowed


def test_ops_incident_types_registered():
    from solaris_ai_nn.ops import incident as I

    for name in (I.HYPOTHESIS_EXPLOSION, I.TOO_MANY_INCONCLUSIVE_TESTS,
                 I.REPEATED_UNSAFE_HYPOTHESES, I.EXCESSIVE_INTERVENTION_RATE,
                 I.NO_HYPOTHESIS_PROGRESS):
        assert name in I.INCIDENT_TYPES
