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
    # + 6 ecology (P23) + 5 active perception (P24)
    # + 6 hypothesis engine (P25) + 9 auto-regeneration (P26)
    # + 6 LOGOS complexity (P27) + 6 conscience runtime (P28)
    # + 7 Pilot-1 soak protocol (P29) + 9 sensory membrane (P31)
    # + 10 Pilot-2 soak protocol (P32) + 7 motor membrane (P33).
    assert len(PermissionScope.ALL) == 125


def test_motor_membrane_scope_defaults():
    ps = PermissionSet.default()
    S = PermissionScope
    # Motor membrane, firewall preflight, dry-run, gridworld, simulated
    # actuators, and Pilot-3 plan are allowed; mixed sensory+gridworld needs
    # approval; no scope ever enables real-world actuation.
    assert ps.allows(S.ENABLE_MOTOR_MEMBRANE)
    assert ps.allows(S.ENABLE_MOTOR_FIREWALL_PREFLIGHT)
    assert ps.allows(S.ENABLE_DRY_RUN_MOTOR_TRACE)
    assert ps.allows(S.ENABLE_GRIDWORLD_MOTOR_SHORT)
    assert ps.allows(S.ENABLE_SIMULATED_ACTUATORS)
    assert ps.allows(S.ENABLE_PILOT3_PLAN_ONLY)
    assert ps.requires_approval(S.ENABLE_MIXED_SENSORY_GRIDWORLD)


def test_pilot2_scope_defaults():
    ps = PermissionSet.default()
    S = PermissionScope
    # Planning/preflight/fixture/nursery/disable/comparison are allowed;
    # mixed short and real soaks require approval.
    assert ps.allows(S.ENABLE_PILOT2)
    assert ps.allows(S.ENABLE_PILOT2_SOURCE_PREFLIGHT)
    assert ps.allows(S.ENABLE_PILOT2_FIXTURE_SHORT)
    assert ps.allows(S.ENABLE_PILOT2_NURSERY_BASELINE)
    assert ps.allows(S.ENABLE_PILOT2_SOURCE_DISABLE)
    assert ps.requires_approval(S.ENABLE_PILOT2_MIXED_SHORT)
    for scope in (S.ENABLE_PILOT2_REAL_READ_ONLY_24H,
                  S.ENABLE_PILOT2_REAL_READ_ONLY_7D,
                  S.ENABLE_PILOT2_REAL_READ_ONLY_30D):
        assert ps.requires_approval(scope)
        assert not ps.allows(scope)


def test_sensory_membrane_scope_defaults():
    ps = PermissionSet.default()
    S = PermissionScope
    # Membrane, dry-run, and JSONL/text/numeric sources are allowed; real
    # on-disk sources, folder polling, and Pilot-2 runs need approval.
    assert ps.allows(S.ENABLE_SENSORY_MEMBRANE)
    assert ps.allows(S.ENABLE_SENSORY_MEMBRANE_DRY_RUN)
    assert ps.allows(S.ENABLE_JSONL_SOURCE)
    assert ps.allows(S.ENABLE_TEXT_SOURCE)
    assert ps.allows(S.ENABLE_NUMERIC_SOURCE)
    assert ps.requires_approval(S.ENABLE_REAL_READ_ONLY_SOURCES)
    assert ps.requires_approval(S.ENABLE_FOLDER_POLL_SOURCE)
    assert ps.requires_approval(S.ENABLE_PILOT2_READ_ONLY_SHORT)
    assert not ps.allows(S.ENABLE_PILOT2_REAL_READ_ONLY_SOAK)


def test_pilot1_scope_defaults():
    ps = PermissionSet.default()
    S = PermissionScope
    # Planning/preflight/drills/retention are allowed; real soaks are off.
    assert ps.allows(S.ENABLE_PILOT1)
    assert ps.allows(S.ENABLE_PILOT1_RESTART_DRILLS)
    assert ps.allows(S.ENABLE_PILOT1_RETENTION_POLICY)
    for scope in (S.ENABLE_PILOT1_24H_REAL, S.ENABLE_PILOT1_7D_REAL,
                  S.ENABLE_PILOT1_30D_REAL, S.ENABLE_PILOT1_MULTI_MONTH_REAL):
        assert ps.requires_approval(scope)
        assert not ps.allows(scope)


def test_conscience_scope_defaults():
    ps = PermissionSet.default()
    S = PermissionScope
    # The orchestrator itself is allowed (bounded, simulation-only); the
    # heavier profiles are opt-in; real long-scale runs are off by default.
    assert ps.allows(S.ENABLE_CONSCIENCE_ORCHESTRATOR)
    assert ps.requires_approval(S.ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE)
    assert ps.requires_approval(S.ENABLE_MONTH_SCALE_DRY_RUN)
    assert ps.requires_approval(S.ENABLE_MONTH_SCALE_REAL_RUN)
    assert ps.requires_approval(S.ENABLE_YEAR_SCALE_PLAN)
    assert ps.requires_approval(S.ENABLE_YEAR_SCALE_REAL_RUN)
    assert not ps.allows(S.ENABLE_MONTH_SCALE_REAL_RUN)
    assert not ps.allows(S.ENABLE_YEAR_SCALE_REAL_RUN)


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


def test_logos_complexity_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_LOGOS_COMPLEXITY)
    assert ps.allows(PermissionScope.ENABLE_FRACTURE_DETECTION)
    assert ps.allows(PermissionScope.ENABLE_SYNTHESIS_CANDIDATES)
    assert ps.allows(PermissionScope.ENABLE_ESC_PROCESS)
    assert ps.allows(PermissionScope.ENABLE_COMPLEXITY_REGULATION)
    # Applying synthesis automatically needs explicit config.
    assert ps.requires_approval(PermissionScope.ENABLE_SAFE_SYNTHESIS)


def test_autoregeneration_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_AUTOREGENERATION)
    assert ps.allows(PermissionScope.ENABLE_STATE_HYGIENE)
    assert ps.allows(PermissionScope.ENABLE_MEMORY_COMPACTION)
    assert ps.allows(PermissionScope.ENABLE_SYMBOL_HYGIENE)
    assert ps.allows(PermissionScope.ENABLE_WORLD_MODEL_HYGIENE)
    assert ps.allows(PermissionScope.ENABLE_HABIT_HYGIENE)
    assert ps.allows(PermissionScope.ENABLE_REPAIR_ROLLBACK)
    # Auto-applying repairs and identity-affecting repair need approval.
    assert ps.requires_approval(PermissionScope.ENABLE_SAFE_AUTO_REPAIR)
    assert ps.requires_approval(PermissionScope.ENABLE_CHECKPOINT_REPAIR)


def test_hypothesis_scope_defaults():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_HYPOTHESIS_ENGINE)
    assert ps.allows(PermissionScope.ENABLE_SELF_EXPERIMENTATION)
    assert ps.allows(PermissionScope.ENABLE_NURSERY_INTERVENTIONS)
    assert ps.allows(PermissionScope.ENABLE_LATENT_HYPOTHESIS_TESTS)
    assert ps.allows(PermissionScope.ENABLE_COUNTERFACTUAL_HYPOTHESIS_TESTS)
    # World-model updates from hypotheses need explicit approval.
    assert ps.requires_approval(
        PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES)
    assert not ps.allows(
        PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES)


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
