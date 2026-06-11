"""Tests for the PermissionSet."""

from __future__ import annotations

import pytest

from solaris_ai_nn.governance.permissions import (
    Permission,
    PermissionScope,
    PermissionSet,
)


def test_default_permissions_allow_bounded_run():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.RUN_BOUNDED)
    assert ps.allows(PermissionScope.ENABLE_EMBODIMENT_SIMULATION)
    assert ps.allows(PermissionScope.ENABLE_SIDECAR_OBSERVE)
    assert ps.allows(PermissionScope.ENABLE_PLASTICITY_DRY_RUN)


def test_active_plasticity_requires_approval():
    ps = PermissionSet.default()
    assert not ps.allows(PermissionScope.ENABLE_PLASTICITY_APPLY)
    assert ps.requires_approval(PermissionScope.ENABLE_PLASTICITY_APPLY)
    assert ps.requires_approval(PermissionScope.RUN_SOAK_24H)
    assert ps.requires_approval(PermissionScope.RUN_SOAK_30D)
    assert ps.requires_approval(PermissionScope.ENABLE_SIDECAR_SUGGESTIONS)


def test_emergency_stop_always_allowed():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.PERFORM_EMERGENCY_STOP)
    assert not ps.requires_approval(PermissionScope.PERFORM_EMERGENCY_STOP)
    # Even an empty permission set allows it -- structurally.
    empty = PermissionSet()
    assert empty.allows(PermissionScope.PERFORM_EMERGENCY_STOP)


def test_emergency_stop_cannot_be_revoked():
    ps = PermissionSet.default()
    with pytest.raises(ValueError):
        ps.revoke(PermissionScope.PERFORM_EMERGENCY_STOP)
    assert ps.allows(PermissionScope.PERFORM_EMERGENCY_STOP)


def test_unknown_scopes_denied_by_default():
    ps = PermissionSet.default()
    assert not ps.allows("teleport_to_production")
    assert ps.requires_approval("teleport_to_production")


def test_grant_and_revoke():
    ps = PermissionSet.default()
    ps.grant("run_continuous_explicit", requires_approval=True)
    assert not ps.allows("run_continuous_explicit")  # approval still needed
    ps.grant("run_continuous_explicit")
    assert ps.allows("run_continuous_explicit")
    ps.revoke("run_continuous_explicit")
    assert not ps.allows("run_continuous_explicit")


def test_all_scopes_in_default_set():
    ps = PermissionSet.default()
    assert set(ps.known_scopes()) == set(PermissionScope.ALL)
    # 13 governance (P12) + 5 latent (P14) + 3 world model (P15)
    # + 4 homeostasis (P16) + 4 executive (P17).
    assert len(PermissionScope.ALL) == 29


def test_executive_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_EXECUTIVE)
    assert ps.allows(PermissionScope.ENABLE_SHORT_HORIZON_PLANNING)
    assert ps.allows(PermissionScope.ENABLE_PROSPECTION)
    assert ps.requires_approval(
        PermissionScope.ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS)


def test_homeostasis_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_HOMEOSTASIS)
    assert ps.allows(PermissionScope.ENABLE_NEED_DRIVEN_SUGGESTIONS)
    assert ps.allows(PermissionScope.ENABLE_AUTO_DETERMINATION)
    assert ps.allows(PermissionScope.ALLOW_SAFE_SHUTDOWN_RECOMMENDATION)


def test_world_model_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_WORLD_MODEL)
    assert ps.allows(PermissionScope.ENABLE_WORLD_MODEL_PREDICTION)
    assert ps.requires_approval(PermissionScope.ENABLE_WORLD_MODEL_PRUNING)


def test_latent_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_LATENT)
    assert ps.allows(PermissionScope.ENABLE_LATENT_DRY_RUN)
    assert ps.allows(PermissionScope.RUN_DREAM_CYCLE)
    assert ps.allows(PermissionScope.RUN_COUNTERFACTUAL_REPLAY)
    assert ps.requires_approval(PermissionScope.ENABLE_LATENT_PLASTICITY)


def test_round_trip():
    ps = PermissionSet.default()
    clone = PermissionSet.from_dict(ps.to_dict())
    assert clone.granted_scopes() == ps.granted_scopes()
    assert isinstance(clone.get(PermissionScope.RUN_BOUNDED), Permission)
