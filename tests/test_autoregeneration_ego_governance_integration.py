"""Integration: ego classification + governance gating of repairs."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    RepairScope,
    make_repair,
)
from solaris_ai_nn.autoregeneration.safety import (
    AutoRegenerationSafetyValidator,
)


def test_source_repair_classified_forbidden():
    # A repair scope of 'forbidden' (or a source target) is refused by
    # safety; the ego would classify it as a forbidden source repair.
    v = AutoRegenerationSafetyValidator()
    source = make_repair(RepairActionType.REBUILD_INDEX,
                         target_ref="src/solaris_ai_nn/core.py")
    assert not v.validate_repair_action(source).safe


def test_identity_repair_requires_governance():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["autoregeneration"] = True
    manifest = ExperimentManifest(
        name="ar", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"identity_affecting_repair": True})
    assert not decision.allowed
    assert any("identity" in r for r in decision.reasons)


def test_governance_blocks_source_repair():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["autoregeneration"] = True
    manifest = ExperimentManifest(
        name="ar", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"source_code_repair": True})
    assert not decision.allowed


def test_safe_auto_repair_needs_config():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["autoregeneration"] = True
    features["safe_auto_repair"] = True
    manifest = ExperimentManifest(
        name="ar", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"safe_auto_repair": True})
    assert not decision.allowed
