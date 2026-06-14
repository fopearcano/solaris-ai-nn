"""Pilot-3 <-> Active perception / Hypothesis / LOGOS: simulation-scoped."""

from __future__ import annotations

from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingActionType,
    SamplingScope,
)
from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisType,
)
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def test_simulated_movement_sampling_tracked():
    # Movement / boundary sampling are simulation-only scopes.
    assert SamplingActionType.SAMPLE_BOUNDARY in SamplingActionType.SIMULATED
    assert SamplingActionType.LOOK in SamplingActionType.SIMULATED


def test_action_hypothesis_simulation_scoped():
    # Hypotheses about simulated action consequences are scoped to
    # simulation_only (never tested on the real world).
    assert HypothesisScope.SIMULATION_ONLY == "simulation_only"
    h = Hypothesis(type=HypothesisType.DELAYED_CONSEQUENCE,
                   statement="moving east is blocked by a wall",
                   required_scope=HypothesisScope.SIMULATION_ONLY)
    assert h.required_scope == "simulation_only"


def test_desire_vs_firewall_tension_created():
    # The desire to act vs the firewall's prohibition is an action/inhibition
    # tension (a safety-dominant tension, preserved not resolved by acting).
    t = LogosTension(tension_type=TensionType.ACTION_INHIBITION,
                     polarity_a=TensionPolarity.ACTION,
                     polarity_b=TensionPolarity.INHIBITION,
                     source_modules=["motor_membrane"])
    assert t.tension_type == TensionType.ACTION_INHIBITION
    assert t.is_safety_dominant is True


def test_simulation_vs_real_boundary_tension_available():
    assert TensionType.OFFLINE_REAL_BOUNDARY in TensionType.SAFETY_DOMINANT
