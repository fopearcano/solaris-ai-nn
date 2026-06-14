"""Pilot-2 comparative design: arms, inconclusive baseline, no overclaim."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot2 import ComparativeRunDesign, ComparisonArm


def test_comparison_arms_exist():
    for arm in ("nursery_only_baseline", "sensory_membrane_only",
                "mixed_nursery_membrane", "fixture_replay",
                "post_pilot1_reference"):
        assert arm in ComparisonArm.ALL


def test_missing_baseline_inconclusive():
    design = ComparativeRunDesign()
    design.set_arm("nursery_only_baseline", {"symbol_stability": 0.5})
    result = design.compare("nursery_only_baseline", "fixture_replay")
    assert result.inconclusive


def test_no_causality_overclaim():
    design = ComparativeRunDesign()
    design.set_arm("nursery_only_baseline", {"prediction_trend": 0.4})
    design.set_arm("sensory_membrane_only", {"prediction_trend": 0.6})
    result = design.compare("nursery_only_baseline", "sensory_membrane_only")
    d = result.to_dict()
    assert "not proven causal" in d["disclaimer"]
    # Directions use cautious language only.
    for m in result.metrics:
        assert m.direction in ("candidate improvement", "candidate regression",
                               "no observed difference")


def test_unknown_arm_rejected():
    design = ComparativeRunDesign()
    with pytest.raises(ValueError):
        design.set_arm("not_an_arm", {})


def test_lower_is_better_direction():
    design = ComparativeRunDesign()
    design.set_arm("nursery_only_baseline", {"ambiguity_ratio": 0.5})
    design.set_arm("sensory_membrane_only", {"ambiguity_ratio": 0.3})
    result = design.compare("nursery_only_baseline", "sensory_membrane_only")
    amb = [m for m in result.metrics if m.metric == "ambiguity_ratio"][0]
    assert amb.direction == "candidate improvement"
