"""Pilot-4 <-> Conscience: profiles exist; plan-only; no actions."""

from __future__ import annotations

from solaris_ai_nn.conscience import RunMode, ScenarioProfileRegistry

_PROFILES = ("pilot4_plan_only", "pilot4_risk_assessment",
             "pilot4_readiness_dossier", "pilot4_decision_gate")


def test_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert set(_PROFILES) <= ids


def test_profiles_do_not_run_cognition_loop():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        profile = reg.get(name)
        ctx = profile.run_context
        # Plan-only month-scale-plan mode -> no cognition loop runs.
        assert ctx.mode == RunMode.MONTH_SCALE_PLAN
        assert ctx.max_steps is None


def test_profiles_do_not_execute_actions():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        constraints = " ".join(reg.get(name).safety_constraints).lower()
        assert "no cognition loop, no actions" in constraints
        assert "real-world actuation prohibited" in constraints


def test_no_real_world_profile():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        constraints = " ".join(reg.get(name).safety_constraints).lower()
        assert "no external authority" in constraints
