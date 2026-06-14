"""Conscience CLI: list/dry-run/run/health/snapshot, all bounded."""

from __future__ import annotations

import json

from solaris_ai_nn.conscience import cli


def test_list_profiles(capsys):
    rc = cli.main(["list-profiles"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    ids = {row["profile_id"] for row in out}
    assert "minimal_smoke" in ids and "month_scale_plan" in ids


def test_run_profile_minimal(tmp_path, capsys):
    rc = cli.main(["run-profile", "--profile", "minimal_smoke",
                   "--state-dir", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["status"] == "completed" and out["ok"] is True


def test_run_profile_governed_blocked(tmp_path, capsys):
    rc = cli.main(["run-profile", "--profile", "month_scale_dry_run",
                   "--state-dir", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert out["status"] == "governance_blocked"


def test_run_profile_governed_with_ack(tmp_path, capsys):
    rc = cli.main(["run-profile", "--profile", "month_scale_dry_run",
                   "--state-dir", str(tmp_path), "--governance-approved"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"] is True


def test_health_check(tmp_path, capsys):
    rc = cli.main(["health-check", "--profile", "minimal_smoke",
                   "--state-dir", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc in (0, 1)
    assert "overall" in out and "checks" in out


def test_dry_run_profile(tmp_path, capsys):
    rc = cli.main(["dry-run-profile", "--profile", "full_developmental_short",
                   "--state-dir", str(tmp_path), "--governance-approved"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["initialized"] is True
    assert "integration_health" in out


def test_snapshot(tmp_path, capsys):
    rc = cli.main(["snapshot", "--profile", "nursery_short",
                   "--state-dir", str(tmp_path), "--governance-approved",
                   "--steps", "8"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["snapshot_id"].startswith("SNAP_")


def test_unknown_profile_returns_error(tmp_path, capsys):
    rc = cli.main(["health-check", "--profile", "nope",
                   "--state-dir", str(tmp_path)])
    assert rc == 2


def test_scenario_main_defaults_to_run(tmp_path, capsys):
    rc = cli.scenario_main(["minimal_smoke", "--state-dir", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["profile_id"] == "minimal_smoke"
