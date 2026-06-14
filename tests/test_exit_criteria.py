"""Pilot-1 exit criteria: success, stop, and the consciousness disclaimer."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import ExitDecisionType, PilotExitCriteria


def _success_obs():
    return {"target_duration_reached": True, "uptime_ratio": 0.99,
            "checkpoint_failure": 0, "unresolved_critical_safety": 0,
            "report_count": 1, "structural_change_score": 0.2,
            "observability_complete": True}


def test_success_criteria_pass():
    decision = PilotExitCriteria().evaluate(_success_obs())
    assert decision.decision == ExitDecisionType.SUCCESS
    assert decision.success is True


def test_failure_criteria_stop():
    decision = PilotExitCriteria().evaluate({"emergency_stop": True})
    assert decision.decision == ExitDecisionType.STOP_FAILURE
    assert decision.must_stop is True


def test_continue_when_only_duration_unmet():
    obs = _success_obs()
    obs["target_duration_reached"] = False
    decision = PilotExitCriteria().evaluate(obs)
    assert decision.decision == ExitDecisionType.CONTINUE


def test_inconclusive_when_metrics_missing():
    decision = PilotExitCriteria().evaluate({"target_duration_reached": True})
    assert decision.decision == ExitDecisionType.INCONCLUSIVE


def test_success_is_not_consciousness():
    decision = PilotExitCriteria().evaluate(_success_obs())
    assert "not evidence of consciousness" in \
        decision.consciousness_disclaimer
