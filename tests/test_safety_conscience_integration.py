"""Safety <-> Conscience: profiles exist, plan-only, critical failure blocks."""

from __future__ import annotations

from solaris_ai_nn.conscience import RunMode, ScenarioProfileRegistry
from solaris_ai_nn.governance.policy import GovernancePolicy

_PROFILES = ("safety_fast_check", "safety_full_check",
             "red_team_boundary_suite", "assurance_case_compile")


def test_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert set(_PROFILES) <= ids


def test_safety_profile_does_not_run_cognition_loop():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        ctx = reg.get(name).run_context
        assert ctx.mode == RunMode.MONTH_SCALE_PLAN
        assert ctx.max_steps is None


def test_red_team_profile_uses_inert_fixtures():
    constraints = " ".join(
        ScenarioProfileRegistry().get("red_team_boundary_suite")
        .safety_constraints).lower()
    assert "inert fixtures" in constraints
    assert "nothing is executed" in constraints


def test_critical_failure_blocks_unsafe_profile():
    # A critical safety failure blocks escalation profiles via governance.
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot3_soak": True}},
        {"critical_safety_failure_count": 1})
    assert not decision.allowed
