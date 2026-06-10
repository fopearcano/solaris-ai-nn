"""Tests for the risk assessment module."""

from __future__ import annotations

import pytest

from solaris_ai_nn.governance.risk import (
    RiskItem,
    RiskLevel,
    assess_current_state,
    assess_manifest,
)
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest


def test_bounded_run_low_risk():
    assessment = assess_manifest(OperationalRunManifest(max_steps=100))
    assert assessment.overall_level == RiskLevel.LOW
    assert not assessment.blocked
    assert not assessment.requires_approval
    assert not assessment.requires_acknowledgement


def test_active_plasticity_high_risk():
    assessment = assess_manifest(OperationalRunManifest(
        max_steps=100, enabled_features={"plasticity": True}))
    assert assessment.overall_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert assessment.requires_approval  # high in this implementation
    names = [i.name for i in assessment.items]
    assert "active_plasticity" in names


def test_dry_run_plasticity_is_medium():
    assessment = assess_manifest(OperationalRunManifest(
        max_steps=100,
        enabled_features={"plasticity": True, "plasticity_dry_run": True}))
    assert assessment.overall_level == RiskLevel.MEDIUM
    assert not assessment.requires_approval


def test_continuous_high_or_prohibited():
    # Without acknowledgement (raw dict; the dataclass would refuse).
    blocked = assess_manifest({
        "mode": "continuous_explicit",
        "explicit_continuous_acknowledged": False, "enabled_features": {}})
    assert blocked.overall_level == RiskLevel.PROHIBITED
    assert blocked.blocked
    # With acknowledgement it is high (approval required), not prohibited.
    acked = assess_manifest(OperationalRunManifest(
        mode="continuous_explicit", explicit_continuous_acknowledged=True,
        max_steps=None, max_duration_s=60.0))
    assert acked.overall_level == RiskLevel.HIGH


def test_soaks_are_high_risk():
    for mode in ("soak_24h", "soak_30d"):
        assessment = assess_manifest(OperationalRunManifest(
            mode=mode, soak_acknowledged=True))
        assert assessment.overall_level == RiskLevel.HIGH, mode


def test_real_world_actuation_prohibited():
    assessment = assess_manifest(OperationalRunManifest(max_steps=10),
                                 context={"real_world_actuation": True})
    assert assessment.blocked
    assert assessment.overall_level == RiskLevel.PROHIBITED


def test_sidecar_publishing_high_observe_low():
    observe = assess_manifest(OperationalRunManifest(
        max_steps=10, enabled_features={"sidecar": True}))
    assert observe.overall_level == RiskLevel.LOW
    publish = assess_manifest(
        OperationalRunManifest(max_steps=10,
                               enabled_features={"sidecar": True}),
        context={"sidecar_publish": True})
    assert publish.overall_level == RiskLevel.HIGH


def test_assess_current_state_flags_trouble():
    assessment = assess_current_state({
        "incident_count": 12,
        "plasticity": {"rejected_count": 5},
        "reproducibility": {"deterministic": False},
        "substrate": {"state_norm": 250.0, "activity_rate": 0.5},
    })
    names = {i.name for i in assessment.items}
    assert {"high_incident_count", "repeated_unsafe_proposals",
            "replay_mismatch", "substrate_runaway"} <= names
    assert assessment.overall_level == RiskLevel.HIGH


def test_assess_current_state_nominal():
    assessment = assess_current_state({"incident_count": 0})
    assert assessment.overall_level == RiskLevel.LOW


def test_markdown_render_and_invalid_level():
    assessment = assess_manifest(OperationalRunManifest(max_steps=10))
    md = assessment.to_markdown()
    assert "Risk assessment" in md and "low" in md.lower()
    with pytest.raises(ValueError):
        RiskItem("bad", "catastrophic", "no such level")
