"""Tests for the PlasticityStep data model."""

from __future__ import annotations

from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityResult,
    PlasticityStep,
    PlasticityTarget,
)


def test_create_step_stores_values():
    step = PlasticityStep(
        target=PlasticityTarget("readout", "learning_rate"),
        change=PlasticityChange(old_value=0.3, new_value=0.4, expected_effect="faster"),
        reason="error high", trigger_source="policy:high_error",
        run_id="r", session_id="s", lifetime_step=10,
    )
    assert step.target.component == "readout"
    assert step.target.parameter == "learning_rate"
    assert step.change.old_value == 0.3
    assert step.change.new_value == 0.4
    assert step.status == "proposed"
    assert step.step_id  # auto-generated
    assert step.timestamp > 0


def test_step_serializes_to_dict():
    step = PlasticityStep(
        target=PlasticityTarget("habit", "reinforcement_rate"),
        change=PlasticityChange(old_value=0.2, new_value=0.25),
    )
    d = step.to_dict()
    assert d["target"]["component"] == "habit"
    assert d["change"]["new_value"] == 0.25
    assert "step_id" in d and "status" in d


def test_step_roundtrip_from_dict():
    step = PlasticityStep(
        target=PlasticityTarget("reservoir", "leak_rate"),
        change=PlasticityChange(old_value=0.3, new_value=0.35),
        reason="tuning",
    )
    back = PlasticityStep.from_dict(step.to_dict())
    assert isinstance(back.target, PlasticityTarget)
    assert isinstance(back.change, PlasticityChange)
    assert back.target.parameter == "leak_rate"
    assert back.change.new_value == 0.35
    assert back.reason == "tuning"


def test_target_label_and_key():
    t = PlasticityTarget("bridge", "exploration_tendency")
    assert t.label() == "bridge.exploration_tendency"
    assert t.key() == ("bridge", "exploration_tendency")


def test_result_to_dict():
    res = PlasticityResult(step_id="abc", status="applied", applied=True,
                           old_value=0.3, new_value=0.4)
    d = res.to_dict()
    assert d["applied"] is True and d["status"] == "applied"
