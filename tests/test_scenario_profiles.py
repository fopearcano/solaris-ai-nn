"""Scenario profiles A--J: bounded, simulation-only, governance flags."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    RunAuthority,
    ScenarioProfile,
    ScenarioProfileRegistry,
)

EXPECTED = {
    "minimal_smoke", "nursery_short", "proto_language_short",
    "active_perception_short", "hypothesis_short", "logos_short",
    "autoregeneration_short", "full_developmental_short",
    "month_scale_plan", "month_scale_dry_run",
}

# Pilot-1 month-scale soak profiles (Prompt 29).
EXPECTED_PILOT = {
    "pilot1_plan_only", "pilot1_preflight", "pilot1_24h_soak",
    "pilot1_7d_soak", "pilot1_30d_soak", "pilot1_simulated_month_dry_run",
}


def test_all_base_profiles_present():
    reg = ScenarioProfileRegistry()
    assert EXPECTED <= set(reg.ids())
    assert EXPECTED_PILOT <= set(reg.ids())


def test_every_profile_is_simulation_only_and_bounded():
    reg = ScenarioProfileRegistry()
    for pid in reg.ids():
        ctx = reg.profiles[pid].run_context
        assert ctx.authority in RunAuthority.RUNNABLE
        assert ctx.authority != RunAuthority.FORBIDDEN
        assert ctx.is_bounded  # plan-only counts as bounded


def test_governed_profiles_flagged():
    reg = ScenarioProfileRegistry()
    governed = set(reg.snapshot()["governed"])
    assert {"full_developmental_short", "month_scale_dry_run",
            "month_scale_plan"} <= governed


def test_month_plan_is_plan_only():
    reg = ScenarioProfileRegistry()
    assert reg.require("month_scale_plan").is_plan_only


def test_profile_syncs_enabled_modules_into_context():
    reg = ScenarioProfileRegistry()
    p = reg.require("nursery_short")
    assert p.run_context.enabled_modules == p.enabled_modules


def test_require_unknown_raises():
    reg = ScenarioProfileRegistry()
    try:
        reg.require("nope")
        assert False
    except KeyError:
        pass


def test_no_real_month_or_year_profile_exists():
    reg = ScenarioProfileRegistry()
    for pid in reg.ids():
        mode = reg.profiles[pid].run_context.mode
        assert mode not in ("month_scale_real", "year_scale_real")


def test_to_dict_roundtrip_fields():
    p = ScenarioProfileRegistry().require("minimal_smoke")
    d = p.to_dict()
    assert d["profile_id"] == "minimal_smoke"
    assert "requires_governance" in d and "expected_metrics" in d
