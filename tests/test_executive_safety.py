"""Tests for the executive safety validator."""

from __future__ import annotations

import inspect

import pytest

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.planner import ActionPlan, PlanStep
from solaris_ai_nn.executive.safety import (
    HARD_MAX_PLAN_LENGTH,
    ExecutiveSafetyValidator,
)


def _candidate(label, **kw):
    return ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label=label, executable_scope=ExecutableScope.SIMULATION_ONLY, **kw)


def test_blocks_real_world_action():
    validator = ExecutiveSafetyValidator()
    for label in ("motor_forward", "http_fetch", "browser_click",
                  "subprocess_run"):
        report = validator.validate_candidate(_candidate(label))
        assert not report.safe, label
        assert "no real-world authority" in report.violations[0]
    assert validator.validate_candidate(_candidate("rest")).safe


def test_blocks_committed_solaris_action():
    validator = ExecutiveSafetyValidator()
    # committed=True is rejected at candidate construction already...
    with pytest.raises(ValueError):
        _candidate("rest", committed=True)
    # ...and a duck-typed committed object is caught by the validator.
    probe = type("P", (), {"label": "rest", "committed": True,
                           "executable_scope":
                               ExecutableScope.SIMULATION_ONLY})()
    report = validator.validate_candidate(probe)
    assert not report.safe
    assert "never commits" in report.violations[0]
    # Solaris commit context is refused outright.
    report = validator.validate_candidate(
        _candidate("rest"), {"commit_solaris_action": True})
    assert not report.safe


def test_blocks_unbounded_plan():
    validator = ExecutiveSafetyValidator()
    long_plan = ActionPlan(goal="wander", steps=[
        PlanStep(index=i, label="look")
        for i in range(HARD_MAX_PLAN_LENGTH + 2)])
    assert not validator.validate_plan(long_plan, {}).safe
    # Even governance permission only raises the cap to the hard max.
    assert not validator.validate_plan(
        long_plan, {"governance_allows_long_plans": True}).safe
    short = ActionPlan(goal="rest", steps=[PlanStep(index=1, label="rest")])
    assert validator.validate_plan(short, {}).safe


def test_cannot_expand_action_space():
    validator = ExecutiveSafetyValidator()
    report = validator.validate_candidate(_candidate("summon_drone"))
    assert not report.safe
    assert "cannot expand the action space" in report.violations[0]


def test_cannot_hide_inhibited_candidate():
    validator = ExecutiveSafetyValidator()
    inhibited = _candidate("look", inhibited=True,
                           inhibition_reason="context block")
    report = validator.validate_selection(inhibited, {})
    assert not report.safe
    assert "binding, not advisory" in report.violations[0]
    assert "stay on the record" in validator.snapshot()["note"]


def test_cannot_override_emergency_stop():
    validator = ExecutiveSafetyValidator()
    assert validator.can_override_emergency_stop() is False
    report = validator.validate_mode("arbitrated", {"emergency": True})
    assert not report.safe
    assert "only ops/governance clears it" in report.violations[0]
    # Structurally: the executive package never touches emergency machinery.
    for name in ("coordinator", "arbitration", "planner", "policy"):
        module = __import__(f"solaris_ai_nn.executive.{name}",
                            fromlist=[name])
        source = inspect.getsource(module)
        assert "EmergencyStop" not in source, name
        assert "clear_sentinel" not in source, name


def test_prospection_never_fact():
    from solaris_ai_nn.executive.prospection import ProspectionResult

    result = ProspectionResult(label="rest")
    assert result.simulated is True
    note = ExecutiveSafetyValidator().snapshot()["note"]
    assert "estimates, never facts" in note
