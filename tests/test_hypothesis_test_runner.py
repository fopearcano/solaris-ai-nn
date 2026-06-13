"""Tests for the hypothesis test runner."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.experiment_design import ExperimentDesign, design_for
from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisStatus,
    HypothesisType,
)
from solaris_ai_nn.hypothesis.test_runner import HypothesisTestRunner


def test_runs_bounded_test(tmp_path):
    runner = HypothesisTestRunner(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.PREDICTION,
                   statement="pattern A predicts B", target_ref="A",
                   required_scope=HypothesisScope.NURSERY_ONLY)
    design = design_for(h)
    ctx = {"prediction_accuracy": 0.4,
           "after": {"prediction_accuracy": 0.6}}
    result = runner.run_design(design, ctx, h)
    assert result.executed
    assert runner.tests_run == 1
    assert (tmp_path / "hypothesis_tests.jsonl").exists()


def test_unsafe_test_marked(tmp_path):
    runner = HypothesisTestRunner(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                   target_ref="t")
    # An unbounded design is refused.
    design = ExperimentDesign(
        hypothesis_id=h.hypothesis_id, scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="up", falsifying_result="down", max_steps=10**9)
    result = runner.run_design(design, {}, h)
    assert result.blocked
    assert h.status == HypothesisStatus.UNSAFE_TO_TEST


def test_insufficient_data_inconclusive(tmp_path):
    runner = HypothesisTestRunner(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE, statement="s",
                   target_ref="edge", required_scope=HypothesisScope.INTERNAL_ONLY)
    design = design_for(h)
    # No metric value present -> inconclusive.
    result = runner.run_design(design, {"step": 0}, h)
    assert result.verdict == "inconclusive"


def test_emergency_blocks_test(tmp_path):
    runner = HypothesisTestRunner(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                   target_ref="t", required_scope=HypothesisScope.NURSERY_ONLY)
    design = design_for(h)
    result = runner.run_design(design, {"emergency": True}, h)
    assert result.blocked
    assert "emergency" in result.blocked_reason


def test_snapshot_shape(tmp_path):
    runner = HypothesisTestRunner(state_dir=tmp_path)
    snap = runner.snapshot()
    assert "tests_run" in snap and "evidence" in snap and "safety" in snap
