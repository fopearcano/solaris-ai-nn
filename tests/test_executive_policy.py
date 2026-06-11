"""Tests for the executive policy / modes."""

from __future__ import annotations

import pytest

from solaris_ai_nn.executive.action_candidates import ActionCandidateType
from solaris_ai_nn.executive.policy import ExecutiveMode, ExecutivePolicy


def test_default_mode_arbitrated():
    policy = ExecutivePolicy()
    assert policy.mode == ExecutiveMode.ARBITRATED
    assert ExecutiveMode.DEFAULT == "arbitrated"
    assert policy.determine_mode({}) == ExecutiveMode.ARBITRATED
    with pytest.raises(ValueError):
        ExecutivePolicy(requested_mode="freewheeling")


def test_emergency_mode_blocks_planning():
    policy = ExecutivePolicy(requested_mode=ExecutiveMode.SHORT_PLAN)
    assert policy.planning_allowed()
    policy.determine_mode({"health_level": "critical"})
    assert policy.mode == ExecutiveMode.EMERGENCY
    assert not policy.planning_allowed()
    assert not policy.execution_allowed()
    assert not policy.allows(ActionCandidateType.SIMULATED_EMBODIED_ACTION)
    assert policy.allows(ActionCandidateType.SAFE_SHUTDOWN_RECOMMENDATION)
    assert policy.allows(ActionCandidateType.OPERATOR_REVIEW_REQUEST)
    assert policy.forced_emergency_total == 1


def test_observe_only_mode_does_not_execute():
    policy = ExecutivePolicy()
    policy.determine_mode({"observe_only": True})
    assert policy.mode == ExecutiveMode.OBSERVE_ONLY
    assert not policy.execution_allowed()
    assert not policy.allows(ActionCandidateType.SIMULATED_EMBODIED_ACTION)
    assert policy.allows(ActionCandidateType.NO_ACTION)


def test_latent_mode_forces_latent_only():
    policy = ExecutivePolicy()
    for latent_mode in ("sleep", "dream", "replay"):
        policy.determine_mode({"latent_mode": latent_mode})
        assert policy.mode == ExecutiveMode.LATENT_ONLY, latent_mode
        assert policy.allows(ActionCandidateType.LATENT_ACTION)
        assert not policy.allows(
            ActionCandidateType.SIMULATED_EMBODIED_ACTION)
    # Back to awake: the requested mode is restored.
    policy.determine_mode({"latent_mode": "awake"})
    assert policy.mode == ExecutiveMode.ARBITRATED


def test_mode_changes_recorded():
    policy = ExecutivePolicy()
    policy.determine_mode({"emergency": True})
    policy.determine_mode({})
    changes = policy.snapshot()["recent_changes"]
    assert changes[0]["to"] == ExecutiveMode.EMERGENCY
    assert "cannot clear it" in changes[0]["reason"]
    assert changes[1]["to"] == ExecutiveMode.ARBITRATED


def test_watchdog_stop_means_no_new_work():
    policy = ExecutivePolicy()
    policy.determine_mode({"watchdog_stop_requested": True})
    assert policy.mode == ExecutiveMode.EMERGENCY
