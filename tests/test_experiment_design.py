"""Tests for experiment design."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.experiment_design import (
    ExperimentDesign,
    ExperimentScope,
    design_for,
)
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType


def test_six_experiment_scopes():
    assert len(ExperimentScope.ALL) == 6
    assert "real_world" not in " ".join(ExperimentScope.ALL)


def test_design_is_bounded():
    h = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                   target_ref="t")
    design = design_for(h)
    assert 1 <= design.max_steps <= 2000
    assert design.scope in ExperimentScope.ALL


def test_falsifying_result_required():
    h = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                   target_ref="t")
    design = design_for(h)
    assert design.falsifying_result
    assert design.expected_result


def test_real_world_scope_absent():
    # ExperimentScope construction rejects unknown scopes.
    import pytest

    with pytest.raises(ValueError):
        ExperimentDesign(hypothesis_id="h", scope="real_world_action",
                         independent_variable="x", observed_variable="y",
                         expected_result="up", falsifying_result="down")


def test_unbounded_design_rejected_by_safety():
    from solaris_ai_nn.hypothesis.safety import HypothesisSafetyValidator

    design = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="down", max_steps=10**9)
    # The design keeps the declared value so safety can refuse it.
    assert not HypothesisSafetyValidator().validate_design(design).safe


def test_intervention_plan_attached_and_bounded():
    h = Hypothesis(type=HypothesisType.STAGNATION_RECOVERY, statement="s",
                   target_ref="stagnation")
    design = design_for(h)
    assert design.intervention_plan is not None
    assert design.intervention_plan.bounded
