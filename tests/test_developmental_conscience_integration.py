"""Developmental: Conscience phase exists; profiles bounded; live needs governance."""

from __future__ import annotations

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry
from solaris_ai_nn.conscience.spine import SpinePhase


def test_conscience_phase_exists():
    assert SpinePhase.DEVELOPMENTAL_LIFE_UPDATE == "developmental_life_update"
    assert SpinePhase.DEVELOPMENTAL_LIFE_UPDATE in SpinePhase.ORDER
    order = SpinePhase.ORDER
    assert order.index(SpinePhase.ACTION_REACTION_UPDATE) \
        < order.index(SpinePhase.DEVELOPMENTAL_LIFE_UPDATE) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def test_profiles_exist_and_bounded():
    reg = ScenarioProfileRegistry()
    for pid in ("developmental_life_fixture_short",
                "developmental_life_epoch_demo",
                "developmental_life_plateau_demo",
                "developmental_life_regression_demo",
                "developmental_life_growth_vs_accumulation_demo",
                "developmental_life_report_only"):
        profile = reg.get(pid)
        assert profile is not None
        assert profile.max_runtime_s and profile.max_runtime_s > 0


def test_live_requires_governance():
    reg = ScenarioProfileRegistry()
    profile = reg.get("developmental_life_fixture_short")
    # Every developmental profile carries a governance requirement.
    assert profile.governance_requirements
    constraints = " ".join(profile.safety_constraints)
    assert "live read-only requires governance" in constraints
