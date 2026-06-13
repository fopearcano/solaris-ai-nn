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
    # + 4 homeostasis (P16) + 4 executive (P17) + 3 ego (P18)
    # + 7 communication (P19) + 5 LLM adapter (P20)
    # + 6 developmental (P21) + 4 proto-language (P22)
    # + 6 ecology (P23) + 5 active perception (P24).
    assert len(PermissionScope.ALL) == 65


def test_executive_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_EXECUTIVE)
    assert ps.allows(PermissionScope.ENABLE_SHORT_HORIZON_PLANNING)
    assert ps.allows(PermissionScope.ENABLE_PROSPECTION)
    assert ps.requires_approval(
        PermissionScope.ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS)


def test_ego_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_EGO_MODEL)
    assert ps.allows(PermissionScope.ENABLE_DIMENSIONAL_COMPARISON)
    assert ps.allows(PermissionScope.ENABLE_SELF_REPORT)


def test_communication_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_DIALOGUE)
    assert ps.allows(PermissionScope.OPERATOR_GENERATE_REPORTS)
    assert ps.allows(PermissionScope.OPERATOR_REQUEST_CHECKPOINT)
    assert ps.allows(PermissionScope.OPERATOR_REQUEST_SAFE_SHUTDOWN)
    assert ps.allows(PermissionScope.OPERATOR_RUN_BOUNDED_BENCHMARK)
    assert ps.allows(PermissionScope.OPERATOR_APPROVE_REQUESTS)
    assert ps.requires_approval(PermissionScope.OPERATOR_SEND_SENSORY_TEXT)


def test_llm_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_LOCAL_LLM_ADAPTER)
    assert ps.allows(PermissionScope.ALLOW_LOCALHOST_LLM_ENDPOINT)
    assert ps.requires_approval(PermissionScope.ALLOW_REMOTE_LLM_ENDPOINT)
    assert ps.allows(PermissionScope.ALLOW_LLM_CLASSIFICATION_ASSIST)
    assert ps.allows(PermissionScope.ALLOW_LLM_REPORT_POLISH)


def test_developmental_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_DEVELOPMENTAL_RUNTIME)
    assert ps.requires_approval(PermissionScope.ENABLE_MONTH_SCALE_TESTING)
    assert ps.requires_approval(PermissionScope.ENABLE_YEAR_SCALE_TESTING)
    assert ps.allows(PermissionScope.ENABLE_MEMORY_COMPRESSION)
    assert ps.allows(PermissionScope.ENABLE_FOSSIL_MEMORY)
    assert ps.requires_approval(
        PermissionScope.ENABLE_DEVELOPMENTAL_PRUNING)


def test_ecology_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_DEVELOPMENTAL_NURSERY)
    assert ps.allows(PermissionScope.ENABLE_ECOLOGY_STREAM)
    assert ps.allows(PermissionScope.ENABLE_DEPRIVATION_WINDOWS)
    assert ps.allows(PermissionScope.ENABLE_ANOMALY_GENERATION)
    assert ps.requires_approval(PermissionScope.ENABLE_MONTH_SCALE_ECOLOGY)
    assert ps.requires_approval(PermissionScope.ENABLE_YEAR_SCALE_ECOLOGY)


def test_active_perception_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_ACTIVE_PERCEPTION)
    assert ps.allows(PermissionScope.ENABLE_NURSERY_SAMPLING_REQUESTS)
    assert ps.allows(PermissionScope.ENABLE_READ_ONLY_STREAM_SAMPLING)
    assert ps.allows(PermissionScope.ENABLE_SIDECAR_OBSERVATION_SAMPLING)
    # Curiosity-driven sampling is off by default; it needs explicit config.
    assert ps.requires_approval(
        PermissionScope.ENABLE_CURIOSITY_DRIVEN_SAMPLING)
    assert not ps.allows(PermissionScope.ENABLE_CURIOSITY_DRIVEN_SAMPLING)


def test_proto_language_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_PROTO_LANGUAGE)
    assert ps.allows(PermissionScope.ENABLE_SYMBOL_EMERGENCE)
    assert ps.allows(PermissionScope.ENABLE_SYMBOLIC_COMPRESSION)
    assert ps.allows(PermissionScope.ENABLE_PROTO_LANGUAGE_TRANSLATION)


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
