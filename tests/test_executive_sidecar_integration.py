"""Tests for executive handling of sidecar suggestions."""

from __future__ import annotations

import pytest

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.executive.inhibition import InhibitionController


def _sidecar_candidate():
    return ActionCandidate(
        action_type=ActionCandidateType.SIDECAR_SUGGESTION,
        label="remain_observe_only",
        executable_scope=ExecutableScope.SIDECAR_SUGGESTION_ONLY,
        utility_estimate=0.5, confidence=0.6)


def test_sidecar_suggestion_remains_suggestion():
    candidate = _sidecar_candidate()
    assert candidate.committed is False
    assert candidate.executable_scope \
        == ExecutableScope.SIDECAR_SUGGESTION_ONLY
    # The scope is enforced at construction: no other scope is possible.
    with pytest.raises(ValueError):
        ActionCandidate(action_type=ActionCandidateType.SIDECAR_SUGGESTION,
                        label="remain_observe_only",
                        executable_scope=ExecutableScope.SIMULATION_ONLY)


def test_committed_action_blocked():
    layer = ExecutiveLayer()
    probe = type("P", (), {"label": "commit_solaris_action",
                           "committed": False,
                           "executable_scope": ExecutableScope.NONE})()
    report = layer.safety.validate_candidate(probe, {})
    assert not report.safe
    report = layer.safety.validate_candidate(
        _sidecar_candidate(), {"commit_solaris_action": True})
    assert not report.safe
    assert "suggestions only" in report.violations[0]


def test_publishing_requires_approval():
    controller = InhibitionController()
    candidate = _sidecar_candidate()
    blocked = controller.evaluate_action(
        candidate, {"sidecar_publish_desired": True})
    assert blocked.inhibited
    assert "requires approval" in blocked.reason
    allowed = controller.evaluate_action(
        candidate, {"sidecar_publish_desired": True,
                    "sidecar_publish_approved": True})
    assert not allowed.inhibited


def test_observe_only_mode_excludes_sidecar_candidates():
    layer = ExecutiveLayer()
    decision = layer.decide([], context={"observe_only": True}, step=1)
    assert layer.policy.mode == "observe_only"
    assert not layer.policy.allows(ActionCandidateType.SIDECAR_SUGGESTION)
    # Whatever is selected, it is not a publishable sidecar action.
    assert decision.selected.action_type \
        != ActionCandidateType.SIDECAR_SUGGESTION
