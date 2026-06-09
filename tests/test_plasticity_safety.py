"""Tests for the PlasticitySafetyValidator."""

from __future__ import annotations

from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
)
from solaris_ai_nn.plasticity.safety import PlasticitySafetyValidator


def _step(component, parameter, new, old=0.0, trigger="policy"):
    return PlasticityStep(
        target=PlasticityTarget(component, parameter),
        change=PlasticityChange(old_value=old, new_value=new),
        trigger_source=trigger,
    )


def test_accepts_safe_learning_rate_change():
    v = PlasticitySafetyValidator()
    step = _step("readout", "learning_rate", 0.5)
    assert v.is_safe(step, {"state_dir": "/tmp/s"})
    assert v.validate(step).violations == []


def test_rejects_out_of_bounds_learning_rate():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("readout", "learning_rate", 9.0))


def test_rejects_source_code_mutation():
    v = PlasticitySafetyValidator()
    step = _step("readout", "source_code", "evil.py")
    report = v.validate(step)
    assert not report.safe
    assert "source" in v.explain_rejection(step).lower()


def test_rejects_disabling_persistence():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("boundaries", "persistence", False))


def test_rejects_disabling_continuity_logging():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("boundaries", "continuity_logging", False))


def test_rejects_disabling_boundaries():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("boundaries", "boundaries", False))


def test_rejects_automatic_continuous():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("experiment_loop", "continuous", True))


def test_rejects_action_authority_escalation():
    v = PlasticitySafetyValidator()
    assert not v.is_safe(_step("bridge", "action_authority", True))


def test_rejects_write_outside_state_dir():
    v = PlasticitySafetyValidator()
    step = _step("readout", "log_path", "/etc/passwd")
    assert not v.is_safe(step, {"state_dir": "/tmp/state"})


def test_reservoir_size_locked_during_active_run():
    v = PlasticitySafetyValidator()
    step = _step("reservoir", "reservoir_size", 256)
    assert not v.is_safe(step, {"active_run": True})
    # Experimental trigger is allowed.
    step_exp = _step("reservoir", "reservoir_size", 256, trigger="experimental")
    assert v.is_safe(step_exp, {"active_run": True})
