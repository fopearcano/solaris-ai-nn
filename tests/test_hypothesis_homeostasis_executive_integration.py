"""Integration: hypothesis pressure -> homeostasis; executive inhibits."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.hypothesis.experiment_design import (
    ExperimentDesign,
    design_to_candidate,
)


def test_unresolved_hypothesis_raises_uncertainty(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"hypothesis": {"inconclusive_count": 5,
                                     "long_lived_unknown_count": 6}})
    assert regulator.state.value("unknown_pressure", 0.0) > 0.0


def test_falsification_surprise_raises_uncertainty(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"hypothesis": {"last_evidence_result": "falsified"}})
    assert regulator.state.value("unknown_pressure", 0.0) >= 0.5


def test_executive_inhibits_unsafe_test():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    # A latent-test candidate maps to run_replay, which the executive
    # inhibits during an emergency/critical state.
    design = ExperimentDesign(
        hypothesis_id="h", scope="latent_replay",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="down", max_steps=20)
    candidate = design_to_candidate(design)
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"emergency": True,
                                                    "health_level": "critical"})
    assert result.inhibited is True


def test_safe_test_candidate_not_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    design = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="down", max_steps=20)
    candidate = design_to_candidate(design)
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"energy": 0.9})
    assert result.inhibited is False
