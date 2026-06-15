"""SensoriumComparison: human vs non-human; missing inconclusive; negatives kept."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    DifferenceStrength,
    SensoriumComparison,
)


def _arm(metrics, blocked=False, inconclusive=False):
    return {"condition": "x", "blocked": blocked, "inconclusive": inconclusive,
            "signature": None, "metrics": metrics}


def test_human_vs_nonhuman_comparison():
    a = _arm({"symbol_family_diversity": 1, "world_node_count": 3,
              "hypothesis_count": 2, "changed_perception_score": 0.3,
              "modality_native_grounding_score": 0.4,
              "human_label_contamination_score": 0.0})
    b = _arm({"symbol_family_diversity": 5, "world_node_count": 30,
              "hypothesis_count": 20, "changed_perception_score": 1.0,
              "modality_native_grounding_score": 0.9,
              "human_label_contamination_score": 0.0})
    result = SensoriumComparison().compare({"human_like": a, "non_human": b,
                                            "mixed": b})
    diff = next(d for d in result.differences
                if d.arm_a == "human_like" and d.arm_b == "non_human")
    assert diff.strength in (DifferenceStrength.MODERATE,
                             DifferenceStrength.STRONG)


def test_missing_data_inconclusive():
    a = _arm({"changed_perception_score": 0.5})
    result = SensoriumComparison().compare({"human_like": a})
    # non_human absent -> the human vs non-human pair is inconclusive.
    diff = next(d for d in result.differences
                if d.arm_a == "human_like" and d.arm_b == "non_human")
    assert diff.strength == DifferenceStrength.INCONCLUSIVE
    assert result.inconclusive_count >= 1


def test_negative_result_preserved():
    same = _arm({"symbol_family_diversity": 3, "world_node_count": 10,
                 "hypothesis_count": 5, "changed_perception_score": 0.5,
                 "modality_native_grounding_score": 0.5,
                 "human_label_contamination_score": 0.0})
    result = SensoriumComparison().compare({"human_like": same,
                                            "non_human": same, "mixed": same})
    diff = next(d for d in result.differences
                if d.arm_a == "human_like" and d.arm_b == "non_human")
    assert diff.strength == DifferenceStrength.NONE
    assert result.negative_result_count >= 1


def test_blocked_arm_inconclusive():
    a = _arm({"changed_perception_score": 0.5})
    b = _arm({"changed_perception_score": 0.5}, blocked=True)
    result = SensoriumComparison().compare({"human_like": a, "non_human": b})
    diff = next(d for d in result.differences
                if d.arm_a == "human_like" and d.arm_b == "non_human")
    assert diff.strength == DifferenceStrength.INCONCLUSIVE
