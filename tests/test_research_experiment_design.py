"""ExperimentDesign: serializes; bounded defaults; limitations required."""

from __future__ import annotations

import pytest

from solaris_ai_nn.research_lab import (
    ExperimentArm,
    ExperimentCondition,
    ExperimentDesign,
)


def test_design_serializes():
    d = ExperimentDesign(title="t", research_question="q")
    data = d.to_dict()
    assert data["title"] == "t"
    assert data["is_real_long_run"] is False
    assert ExperimentDesign.from_dict(data).title == "t"


def test_bounded_defaults():
    d = ExperimentDesign(title="t", research_question="q")
    assert d.max_steps > 0
    assert d.is_real_long_run is False


def test_unbounded_rejected():
    with pytest.raises(ValueError):
        ExperimentDesign(title="t", research_question="q", max_steps=0)
    with pytest.raises(ValueError):
        ExperimentDesign(title="t", research_question="q", max_steps=999999)


def test_limitations_required():
    d = ExperimentDesign(title="t", research_question="q")
    assert d.limitations
    joined = " ".join(d.limitations).lower()
    assert "consciousness" in joined


def test_conditions_exist():
    for c in ("minimal_runtime", "full_runtime", "nursery_only",
              "sensory_membrane", "gridworld_embodiment", "ablation_run",
              "baseline_run"):
        assert c in ExperimentCondition.ALL


def test_arms_added():
    d = ExperimentDesign(title="t", research_question="q")
    d.add_arm(ExperimentArm("full", "variant", "full"))
    assert len(d.arms) == 1
