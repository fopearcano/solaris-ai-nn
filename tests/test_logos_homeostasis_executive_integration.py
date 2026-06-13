"""Integration: complexity pressure -> homeostasis; synthesis -> executive."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisCandidate,
    SynthesisType,
    synthesis_to_candidate,
)


def test_complexity_pressure_reaches_homeostasis(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"logos": {"complexity_band": "overloaded",
                                "unresolved_tension_count": 5}})
    assert regulator.state.value("complexity_pressure", 0.0) > 0.0
    assert regulator.state.value("stabilization_pressure", 0.0) > 0.0


def test_unresolved_tension_raises_unknown_pressure(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"logos": {"complexity_band": "complex_unstable",
                                "unresolved_tension_count": 6}})
    assert regulator.state.value("unresolved_tension_pressure", 0.0) > 0.0


def test_synthesis_becomes_executive_candidate():
    candidate = synthesis_to_candidate(SynthesisCandidate(
        tension_id="t",
        synthesis_type=SynthesisType.STABILIZE_EXECUTIVE_POLICY))
    assert candidate.committed is False
    assert candidate.label == "stabilize"


def test_unsafe_candidate_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    # A latent-replay synthesis maps to run_replay, inhibited in emergency.
    candidate = synthesis_to_candidate(SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.REQUEST_LATENT_REPLAY))
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"emergency": True,
                                                    "health_level": "critical"})
    assert result.inhibited is True


def test_safe_candidate_not_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    candidate = synthesis_to_candidate(SynthesisCandidate(
        tension_id="t",
        synthesis_type=SynthesisType.STABILIZE_EXECUTIVE_POLICY))
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"energy": 0.9})
    assert result.inhibited is False
