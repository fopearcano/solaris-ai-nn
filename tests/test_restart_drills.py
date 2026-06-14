"""Pilot-1 restart drills: simulated restarts, identity continuity checks."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import (
    DrillOutcome,
    RestartDrillRunner,
    RestartDrillType,
)


def _runner(tmp_path):
    runner = RestartDrillRunner(base_dir=str(tmp_path))
    runner.seed_identity("RUN_A", session_id="SESS_A")
    return runner


def test_graceful_restart_simulated(tmp_path):
    runner = _runner(tmp_path)
    result = runner.run(RestartDrillType.GRACEFUL_SHUTDOWN_RESTART,
                        identity_after={"run_id": "RUN_A"})
    assert result.outcome == DrillOutcome.PASS
    assert result.identity_continuous


def test_crash_gap_simulated_via_metadata(tmp_path):
    runner = _runner(tmp_path)
    result = runner.run(RestartDrillType.SIMULATED_CRASH_GAP,
                        identity_after={"run_id": "RUN_A", "gap_seconds": 300})
    assert result.outcome == DrillOutcome.PASS
    assert result.evidence["simulated_gap_seconds"] == 300


def test_identity_break_fails_drill(tmp_path):
    runner = _runner(tmp_path)
    result = runner.run(RestartDrillType.GRACEFUL_SHUTDOWN_RESTART,
                        identity_after={"run_id": "DIFFERENT"})
    assert result.outcome == DrillOutcome.FAIL
    assert not result.identity_continuous


def test_checkpoint_restore_inconclusive_without_checkpoint(tmp_path):
    runner = _runner(tmp_path)
    result = runner.run(RestartDrillType.CHECKPOINT_RESTORE)
    assert result.outcome == DrillOutcome.INCONCLUSIVE


def test_run_all_and_snapshot(tmp_path):
    runner = _runner(tmp_path)
    results = runner.run_all()
    assert len(results) == len(RestartDrillType.ALL)
    snap = runner.snapshot()
    assert snap["drill_count"] == len(results)


def test_unknown_drill_rejected(tmp_path):
    runner = _runner(tmp_path)
    try:
        runner.run("teleport")
        assert False
    except ValueError:
        pass
