"""Action-reaction: Conscience phase exists; research protocols exist."""

from __future__ import annotations

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry
from solaris_ai_nn.conscience.spine import SpinePhase
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_conscience_phase_exists():
    assert SpinePhase.ACTION_REACTION_UPDATE == "action_reaction_update"
    assert SpinePhase.ACTION_REACTION_UPDATE in SpinePhase.ORDER
    order = SpinePhase.ORDER
    assert order.index(SpinePhase.SAFE_INTERNAL_ACTION_ARBITRATION) \
        < order.index(SpinePhase.ACTION_REACTION_UPDATE) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def test_conscience_profiles_exist():
    reg = ScenarioProfileRegistry()
    for pid in ("action_reaction_fixture_short", "habit_formation_demo",
                "action_inhibition_demo", "no_effect_action_demo",
                "blocked_action_reaction_demo", "action_reaction_report_only"):
        assert reg.get(pid) is not None


def test_research_protocols_exist():
    for name in ("action_reaction", "consequence_learning",
                 "effect_learning_evaluation", "habit_formation",
                 "action_inhibition", "no_effect_action",
                 "action_reaction_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])
