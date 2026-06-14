"""Pilot3ComparativeDesign: arms exist; no causality overclaim; sim-scoped."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import Pilot3ComparativeDesign, Pilot3ComparisonArm


def test_comparison_arms_exist():
    assert {"no_body_internal_only", "read_only_sensory",
            "gridworld_simulated_body", "mixed_sensory_gridworld",
            "dry_run_motor_trace"} == set(Pilot3ComparisonArm.ALL)


def test_no_causality_overclaim():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.READ_ONLY_SENSORY,
               {"action_grounded_proto_symbol_count": 1})
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3})
    result = cd.action_vs_perception().to_dict()
    assert "not proven causal" in result["disclaimer"]
    assert "simulation-scoped" in result["disclaimer"]


def test_simulation_scope_real_world_evidence_zero():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3,
                "real_world_action_evidence": 99})  # forced to 0 on set
    assert cd.arms[Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY][
        "real_world_action_evidence"] == 0


def test_missing_baseline_inconclusive():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3})
    result = cd.action_vs_perception()
    assert result.inconclusive is True


def test_metric_direction_is_cautious():
    cd = Pilot3ComparativeDesign()
    cd.set_arm(Pilot3ComparisonArm.READ_ONLY_SENSORY,
               {"action_grounded_proto_symbol_count": 1})
    cd.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY,
               {"action_grounded_proto_symbol_count": 3})
    metrics = cd.action_vs_perception().metrics
    assert any(m.direction == "candidate improvement" for m in metrics)
