"""Pilot-1 <-> Conscience: profiles exist, plan-only starts no long run."""

from __future__ import annotations

from solaris_ai_nn.conscience import ScenarioProfileRegistry, ScenarioRunner
from solaris_ai_nn.governance.policy import GovernancePolicy

_PILOT_PROFILES = {
    "pilot1_plan_only", "pilot1_preflight", "pilot1_24h_soak",
    "pilot1_7d_soak", "pilot1_30d_soak", "pilot1_simulated_month_dry_run",
}


def test_pilot_profiles_exist():
    reg = ScenarioProfileRegistry()
    assert _PILOT_PROFILES <= set(reg.ids())


def test_plan_only_is_plan_only():
    reg = ScenarioProfileRegistry()
    assert reg.require("pilot1_plan_only").is_plan_only


def test_plan_only_does_not_run_long(tmp_path):
    gov = GovernancePolicy()  # enable_pilot1 granted by default
    runner = ScenarioRunner(state_dir=str(tmp_path), output_dir=str(tmp_path),
                            governance=gov)
    result = runner.run_profile("pilot1_plan_only")
    assert result.plan_only is True
    assert result.steps == 0


def test_preflight_profile_runs_bounded(tmp_path):
    gov = GovernancePolicy()
    runner = ScenarioRunner(state_dir=str(tmp_path), output_dir=str(tmp_path),
                            governance=gov)
    result = runner.run_profile("pilot1_preflight")
    assert result.ok
    assert 0 < result.steps <= 60


def test_30d_soak_blocked_without_governance(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("pilot1_30d_soak")
    assert result.status == "governance_blocked"


def test_30d_soak_runs_with_governance(tmp_path):
    gov = GovernancePolicy()
    gov.permissions.grant("enable_pilot1_30d_real")
    runner = ScenarioRunner(state_dir=str(tmp_path), output_dir=str(tmp_path),
                            governance=gov)
    result = runner.run_profile("pilot1_30d_soak")
    assert result.ok
