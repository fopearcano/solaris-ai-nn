"""Pilot-3 <-> Pilot-2 / post-pilot: read-only baseline comparison."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import (
    EmbodiedPostAnalyzer,
    Pilot3ComparativeDesign,
    Pilot3ComparisonArm,
)


def test_pilot2_baseline_comparison_works():
    # A Pilot-2 read-only grounding baseline feeds the read_only_sensory arm.
    pilot2_baseline = {"action_grounded_proto_symbol_count": 1,
                       "simulated_consequence_prediction_accuracy": 0.3}
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.READ_ONLY_SENSORY, pilot2_baseline)
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3,
                "simulated_consequence_prediction_accuracy": 0.6})
    result = cd.action_vs_perception()
    assert result.inconclusive is False
    assert result.metrics
    # Differences are cautious, simulation-scoped.
    assert result.to_dict()["real_world_action_evidence"] == 0


def test_missing_baseline_inconclusive():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3})
    result = cd.action_vs_perception()
    assert result.inconclusive is True
    # The post-analyzer marks an inconclusive comparison.
    post = EmbodiedPostAnalyzer().analyze(comparison=result)
    assert any("inconclusive" in r for r in post.reasons)


def test_post_analysis_uses_comparison():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.READ_ONLY_SENSORY,
               {"action_grounded_proto_symbol_count": 1})
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 4})
    comp = cd.action_vs_perception()
    post = EmbodiedPostAnalyzer().analyze(comparison=comp,
                                          consequence_prediction_accuracy=0.6,
                                          baseline_prediction_accuracy=0.3)
    assert post.exceeded_read_only_baseline is True
