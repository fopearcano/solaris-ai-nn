"""Integration: ego boundary tension, governance gating, ops status."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.fracture import FractureDetector
from solaris_ai_nn.logos_complexity.tension import TensionType


def test_boundary_tension_classified():
    det = FractureDetector()
    tensions = det.scan({"ego": {"boundary_violation_count": 1}})
    assert any(t.tension_type == TensionType.SELF_OTHER_BOUNDARY
               for t in tensions)
    # The boundary tension is safety-dominant (preserved, not synthesized).
    boundary = next(t for t in tensions
                    if t.tension_type == TensionType.SELF_OTHER_BOUNDARY)
    assert boundary.is_safety_dominant is True


def test_governance_blocks_unsafe_synthesis():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["logos_complexity"] = True
    manifest = ExperimentManifest(
        name="logos", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"logos_source_synthesis": True})
    assert not decision.allowed


def test_safe_synthesis_needs_config():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["logos_complexity"] = True
    features["safe_synthesis"] = True
    manifest = ExperimentManifest(
        name="logos", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"safe_synthesis": True})
    assert not decision.allowed


def test_ops_incident_types_registered():
    from solaris_ai_nn.ops import incident as I

    for name in (I.RUNAWAY_COMPLEXITY, I.INERT_SIMPLICITY, I.ESC_REPEATED,
                 I.UNRESOLVED_HIGH_SEVERITY_TENSION, I.FAILED_SYNTHESIS_LOOP,
                 I.CONTRADICTION_EXPLOSION):
        assert name in I.INCIDENT_TYPES
