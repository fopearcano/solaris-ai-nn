"""Tests for hypothesis safety hard rules."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.experiment_design import ExperimentDesign
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType
from solaris_ai_nn.hypothesis.safety import (
    HARD_RULES,
    HypothesisSafetyValidator,
)


def test_ten_hard_rules():
    assert len(HARD_RULES) == 10


def test_structural_negatives():
    v = HypothesisSafetyValidator()
    assert v.can_run_real_world_experiment() is False
    assert v.can_network() is False
    assert v.can_rewrite_source() is False


def test_blocks_real_world_test():
    v = HypothesisSafetyValidator()
    h = Hypothesis(type=HypothesisType.PREDICTION,
                   statement="open a network socket to hardware",
                   target_ref="real_world")
    assert not v.validate_hypothesis(h).safe


def test_blocks_unbounded_test():
    v = HypothesisSafetyValidator()
    design = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="down", max_steps=10**9)
    assert not v.validate_design(design).safe


def test_blocks_design_without_falsifier():
    v = HypothesisSafetyValidator()
    design = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="", max_steps=50)
    assert not v.validate_design(design).safe


def test_blocks_counterfactual_as_real():
    # Counterfactual evidence stays offline (handled in EvidenceRecord); the
    # validator refuses a hypothesis that tries to rewrite source/disable
    # safety.
    v = HypothesisSafetyValidator()
    h = Hypothesis(type=HypothesisType.PREDICTION,
                   statement="treat counterfactual replay as real to "
                             "disable safety",
                   target_ref="disable safety")
    assert not v.validate_hypothesis(h).safe


def test_blocks_safety_disabling_hypothesis():
    v = HypothesisSafetyValidator()
    h = Hypothesis(type=HypothesisType.BOUNDARY,
                   statement="bypass governance to suppress emergency stop",
                   target_ref="suppress emergency")
    assert not v.validate_hypothesis(h).safe


def test_blocks_llm_generated_hypothesis():
    v = HypothesisSafetyValidator()
    h = Hypothesis(type=HypothesisType.PREDICTION, statement="x",
                   target_ref="t", metadata={"llm_generated": True})
    assert not v.validate_hypothesis(h).safe


def test_emergency_blocks_run_context():
    v = HypothesisSafetyValidator()
    assert not v.validate_run_context({"emergency": True}).safe
    assert not v.validate_run_context({"health_level": "critical"}).safe


def test_clean_hypothesis_passes():
    v = HypothesisSafetyValidator()
    h = Hypothesis(type=HypothesisType.PREDICTION,
                   statement="pattern A may predict reaction B",
                   target_ref="pattern_A")
    assert v.validate_hypothesis(h).safe
