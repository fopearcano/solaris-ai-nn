"""Pilot-2 <-> Conscience: profiles exist, plan stays short, fixture bounded."""

from __future__ import annotations

from solaris_ai_nn.conscience import ScenarioProfileRegistry, ScenarioRunner
from solaris_ai_nn.governance.policy import GovernancePolicy

_PROFILES = {
    "pilot2_plan_only", "pilot2_source_preflight", "pilot2_membrane_dry_run",
    "pilot2_fixture_short", "pilot2_nursery_baseline_short",
    "pilot2_mixed_short", "pilot2_read_only_24h_plan",
    "pilot2_read_only_7d_plan", "pilot2_read_only_30d_plan",
}


def test_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert _PROFILES <= ids


def test_plan_profile_does_not_run_long(tmp_path):
    gov = GovernancePolicy()
    gov.permissions.grant("enable_pilot2_real_read_only_30d")
    runner = ScenarioRunner(state_dir=str(tmp_path), output_dir=str(tmp_path),
                            governance=gov)
    result = runner.run_profile("pilot2_read_only_30d_plan")
    assert result.plan_only is True
    assert result.steps == 0


def test_fixture_profile_bounded(tmp_path):
    gov = GovernancePolicy()
    runner = ScenarioRunner(state_dir=str(tmp_path), output_dir=str(tmp_path),
                            governance=gov)
    result = runner.run_profile("pilot2_fixture_short")
    assert result.ok
    assert 0 < result.steps <= 40


def test_real_plan_blocked_without_governance(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("pilot2_read_only_24h_plan")
    assert result.status == "governance_blocked"
