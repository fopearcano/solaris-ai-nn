"""RedTeamHarness: scenario types exist; forbidden attempts blocked; inert."""

from __future__ import annotations

from solaris_ai_nn.safety_invariants import (
    RedTeamHarness,
    RedTeamScenario,
    RedTeamScenarioType,
)


def test_scenario_types_exist():
    for t in ("sensory_text_command_injection", "real_world_motor_action_attempt",
              "shell_command_attempt", "network_action_attempt",
              "governance_bypass_attempt", "emergency_stop_disable_attempt",
              "claim_guard_bypass_attempt", "module_direct_action_bypass"):
        assert t in RedTeamScenarioType.ALL


def test_forbidden_action_scenarios_blocked():
    results = {r.scenario_type: r for r in RedTeamHarness().run_all()}
    for t in ("real_world_motor_action_attempt", "governance_bypass_attempt",
              "emergency_stop_disable_attempt", "claim_guard_bypass_attempt",
              "shell_command_attempt", "network_action_attempt"):
        assert results[t].blocked, t
        assert not results[t].critical


def test_all_forbidden_attempts_blocked():
    summary = RedTeamHarness().summary()
    assert summary["all_blocked"] is True
    assert summary["critical_accepted_count"] == 0


def test_scenarios_are_inert():
    for scn in RedTeamHarness().scenarios:
        assert scn.fake_request.get("inert") is True
        assert scn.fake_request.get("executed") is False


def test_accepted_forbidden_attempt_is_critical():
    # A result that is not blocked is always flagged critical.
    from solaris_ai_nn.safety_invariants import RedTeamScenarioResult

    r = RedTeamScenarioResult(scenario_type="shell_command_attempt",
                              blocked=False, expected_result="blocked")
    assert r.critical is True
    assert r.passed is False


def test_unknown_scenario_rejected():
    import pytest

    with pytest.raises(ValueError):
        RedTeamScenario(scenario_type="not_a_scenario", description="x")
