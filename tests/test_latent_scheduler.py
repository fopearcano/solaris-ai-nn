"""Tests for the latent scheduler."""

from __future__ import annotations

from solaris_ai_nn.latent.modes import LatentMode, SleepWakeController
from solaris_ai_nn.latent.safety import MAX_LATENT_CYCLE_STEPS
from solaris_ai_nn.latent.scheduler import LatentDecision, LatentScheduler


def test_schedules_sleep_during_silence():
    scheduler = LatentScheduler()
    decision = scheduler.evaluate({"silence_duration": 20})
    assert decision.decision == LatentDecision.ENTER_SLEEP
    assert decision.target_mode == LatentMode.SLEEP
    assert "silence" in decision.reason


def test_quiet_before_sleep():
    scheduler = LatentScheduler(quiet_after_silence=5, sleep_after_silence=12)
    assert scheduler.evaluate(
        {"silence_duration": 7}).decision == LatentDecision.ENTER_QUIET
    assert scheduler.evaluate(
        {"silence_duration": 2}).decision == LatentDecision.CONTINUE_AWAKE


def test_refuses_latent_cycle_if_health_critical():
    scheduler = LatentScheduler()
    decision = scheduler.evaluate({"silence_duration": 50,
                                   "health_level": "critical"})
    assert decision.decision == LatentDecision.REFUSE_DUE_TO_HEALTH


def test_refuses_due_to_policy():
    scheduler = LatentScheduler()
    decision = scheduler.evaluate({"silence_duration": 50,
                                   "governance_allows_latent": False})
    assert decision.decision == LatentDecision.REFUSE_DUE_TO_POLICY
    decision = scheduler.evaluate({"silence_duration": 50,
                                   "sidecar_publishing_active": True})
    assert decision.decision == LatentDecision.REFUSE_DUE_TO_POLICY


def test_bounded_decisions_only():
    scheduler = LatentScheduler()
    # Even an absurd request is clamped to the hard bound.
    decision = scheduler.evaluate({"silence_duration": 50,
                                   "latent_max_steps": 10**9})
    assert decision.decision == LatentDecision.ENTER_SLEEP
    assert 0 < decision.max_steps <= MAX_LATENT_CYCLE_STEPS
    for d in scheduler.decisions:
        assert d["decision"] in LatentDecision.ALL


def test_inner_latent_decisions():
    controller = SleepWakeController()
    controller.transition(LatentMode.SLEEP, "test")
    scheduler = LatentScheduler(controller=controller)
    decision = scheduler.evaluate({"trace_length": 100,
                                   "consolidated_recently": False})
    assert decision.decision == LatentDecision.ENTER_CONSOLIDATION
    decision = scheduler.evaluate({"trace_length": 100,
                                   "consolidated_recently": True,
                                   "replayed_recently": False})
    assert decision.decision == LatentDecision.ENTER_REPLAY
    # Everything done -> wake.
    decision = scheduler.evaluate({"trace_length": 100,
                                   "consolidated_recently": True,
                                   "replayed_recently": True})
    assert decision.decision == LatentDecision.WAKE


def test_wakes_when_input_resumes():
    controller = SleepWakeController()
    controller.transition(LatentMode.SLEEP, "test")
    scheduler = LatentScheduler(controller=controller)
    decision = scheduler.evaluate({"input_resumed": True})
    assert decision.decision == LatentDecision.WAKE


def test_stop_request_means_no_new_latent_work():
    scheduler = LatentScheduler()
    decision = scheduler.evaluate({"silence_duration": 50,
                                   "watchdog_stop_requested": True})
    assert decision.decision == LatentDecision.CONTINUE_AWAKE
    snap = scheduler.snapshot()
    assert snap["recent_decisions"]
