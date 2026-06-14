"""Research <-> Conscience: profiles exist, bounded, report-only is plan-only."""

from __future__ import annotations

from solaris_ai_nn.conscience import RunMode, ScenarioProfileRegistry

_PROFILES = ("research_minimal_smoke", "research_full_short",
             "research_ablation_short", "research_baseline_random",
             "research_baseline_fixed", "research_gridworld_ablation",
             "research_sensory_ablation", "research_report_only")


def test_research_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert set(_PROFILES) <= ids


def test_bounded_profiles_run():
    reg = ScenarioProfileRegistry()
    short = reg.get("research_full_short")
    assert short.run_context.max_steps is not None
    assert short.run_context.max_steps > 0


def test_report_only_profile_does_not_run_cognition_loop():
    reg = ScenarioProfileRegistry()
    report = reg.get("research_report_only")
    # The report-only profile is plan-only (no bounded cognition loop).
    assert report.run_context.mode == RunMode.MONTH_SCALE_PLAN
    assert report.run_context.max_steps is None


def test_no_research_profile_enables_external_authority():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        constraints = " ".join(reg.get(name).safety_constraints).lower()
        assert "no external authority" in constraints
        assert "no real long soak" in constraints
