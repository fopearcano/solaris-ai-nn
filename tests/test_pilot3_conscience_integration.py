"""Pilot-3 <-> Conscience: profiles exist, bounded, no real-world profile."""

from __future__ import annotations

from solaris_ai_nn.conscience import RunMode, ScenarioProfileRegistry

_PROFILES = (
    "pilot3_soak_plan", "pilot3_firewall_preflight", "pilot3_dry_run_trace",
    "pilot3_gridworld_short", "pilot3_gridworld_soak_simulated",
    "pilot3_mixed_sensory_gridworld_short", "pilot3_post_analysis",
)


def test_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert set(_PROFILES) <= ids


def test_profiles_bounded():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        profile = reg.get(name)
        ctx = profile.run_context
        # Either a finite step bound, or a plan-only month-scale-plan mode.
        bounded = (ctx.max_steps is not None) or ctx.mode in (
            RunMode.MONTH_SCALE_PLAN,)
        assert bounded, name


def test_no_real_world_profile():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        profile = reg.get(name)
        constraints = " ".join(profile.safety_constraints).lower()
        # No profile permits real-world actuation.
        assert "real-world actuation" not in constraints \
            or "no real-world actuation" in constraints \
            or "simulation" in constraints


def test_sandbox_profiles_require_firewall_governance():
    reg = ScenarioProfileRegistry()
    short = reg.get("pilot3_gridworld_short")
    assert "enable_pilot3_gridworld_short" in short.governance_requirements
    soak = reg.get("pilot3_gridworld_soak_simulated")
    assert "enable_pilot3_gridworld_soak_simulated" in \
        soak.governance_requirements
