"""Scenario runner: runs profiles bounded, logs runs, gates governed ones."""

from __future__ import annotations

import json
from pathlib import Path

from solaris_ai_nn.conscience import ScenarioExitStatus, ScenarioRunner
from solaris_ai_nn.governance.policy import GovernancePolicy


def test_minimal_smoke_completes(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path / "s"),
                            output_dir=str(tmp_path / "o"))
    result = runner.run_profile("minimal_smoke")
    assert result.status == ScenarioExitStatus.COMPLETED
    assert result.ok and result.steps > 0


def test_governed_profile_blocked_without_governance(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("month_scale_dry_run")
    assert result.status == ScenarioExitStatus.GOVERNANCE_BLOCKED
    assert not result.ok


def test_governed_profile_runs_with_explicit_approval(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("full_developmental_short",
                                governance_approved=True)
    assert result.ok


def test_governed_profile_runs_when_governance_enables_scope(tmp_path):
    gov = GovernancePolicy()
    gov.permissions.grant("enable_month_scale_dry_run")
    runner = ScenarioRunner(state_dir=str(tmp_path), governance=gov)
    result = runner.run_profile("month_scale_dry_run")
    assert result.ok


def test_plan_only_profile_reports_plan(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("month_scale_plan", governance_approved=True)
    assert result.status == ScenarioExitStatus.PLAN_ONLY
    assert result.steps == 0


def test_unknown_profile_is_error(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path))
    result = runner.run_profile("nope")
    assert result.status == ScenarioExitStatus.ERROR


def test_runs_log_and_report_written(tmp_path):
    out = tmp_path / "o"
    runner = ScenarioRunner(state_dir=str(tmp_path / "s"), output_dir=str(out))
    result = runner.run_profile("minimal_smoke")
    log = out / "scenario_runs.jsonl"
    assert log.exists()
    lines = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
    assert lines and lines[-1]["profile_id"] == "minimal_smoke"
    assert result.report_path and Path(result.report_path).exists()


def test_run_all_short_skips_plan_and_governed(tmp_path):
    runner = ScenarioRunner(state_dir=str(tmp_path / "s"),
                            output_dir=str(tmp_path / "o"))
    results = runner.run_all_short()
    ids = {r.profile_id for r in results}
    assert "minimal_smoke" in ids
    assert "month_scale_plan" not in ids  # plan-only skipped
    assert all(r.ok for r in results)
