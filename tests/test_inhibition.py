"""Tests for the inhibition controller."""

from __future__ import annotations

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.desire_queue import DesireQueue
from solaris_ai_nn.executive.inhibition import InhibitionController
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _probe(label, action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
           scope=ExecutableScope.SIMULATION_ONLY, cost=0.2):
    return ActionCandidate(action_type=action_type, label=label,
                           executable_scope=scope, expected_cost=cost)


def test_governance_blocks_prohibited_action():
    controller = InhibitionController()
    result = controller.evaluate_action(
        _probe("explore_safely"),
        {"prohibited_actions": ["explore_safely"]})
    assert result.inhibited and result.family == "governance"
    result = controller.evaluate_action(
        _probe("rest"), {"governance_blocks": {"rest": "operator pause"}})
    assert result.inhibited and "operator pause" in result.reason


def test_safety_blocks_real_world_action():
    controller = InhibitionController()
    result = controller.evaluate_action(_probe("motor_forward"), {})
    assert result.inhibited and result.family == "safety"
    unknown = controller.evaluate_action(_probe("teleport"), {})
    assert unknown.inhibited
    assert unknown.rule_id == "safety_unknown_action"


def test_latent_mode_blocks_external_action():
    controller = InhibitionController()
    for mode in ("sleep", "dream", "replay"):
        result = controller.evaluate_action(_probe("look"),
                                            {"latent_mode": mode})
        assert result.inhibited, mode
        assert result.family == "context"
    # Internal maintenance stays allowed during latent modes.
    internal = _probe("consolidate_memory",
                      action_type=ActionCandidateType.LATENT_ACTION,
                      scope=ExecutableScope.INTERNAL_ONLY, cost=0.0)
    assert not controller.evaluate_action(internal,
                                          {"latent_mode": "sleep"}).inhibited


def test_resource_and_emergency_inhibition():
    controller = InhibitionController()
    poor = controller.evaluate_action(_probe("look", cost=0.5),
                                      {"energy": 0.1})
    assert poor.inhibited and poor.family == "resource"
    emergency = controller.evaluate_action(
        _probe("explore_safely"), {"health_level": "critical"})
    assert emergency.inhibited and emergency.rule_id == "context_emergency"
    watchdog = controller.evaluate_action(
        _probe("look"), {"watchdog_stop_requested": True})
    assert watchdog.inhibited and watchdog.rule_id == "resource_watchdog"


def test_blocked_reason_recorded():
    controller = InhibitionController()
    queue = DesireQueue()
    queue.push(DesireCandidate(proposal="explore_safely", motivation=0.8))
    queue.push(DesireCandidate(proposal="rest", motivation=0.5))
    inhibited = controller.apply_to_queue(queue,
                                          {"health_level": "critical"})
    assert inhibited == 1
    entry = [i for i in queue.items if i.inhibited][0]
    assert "context_emergency" in entry.inhibition_reason
    snap = controller.snapshot()
    assert snap["inhibitions_total"] >= 1
    assert all(row["reason"] for row in snap["recent"])


def test_sidecar_publishing_inhibited_without_approval():
    controller = InhibitionController()
    suggestion = ActionCandidate(
        action_type=ActionCandidateType.SIDECAR_SUGGESTION,
        label="remain_observe_only",
        executable_scope=ExecutableScope.SIDECAR_SUGGESTION_ONLY)
    blocked = controller.evaluate_action(
        suggestion, {"sidecar_publish_desired": True})
    assert blocked.inhibited and blocked.family == "governance"
    allowed = controller.evaluate_action(
        suggestion, {"sidecar_publish_desired": True,
                     "sidecar_publish_approved": True})
    assert not allowed.inhibited
