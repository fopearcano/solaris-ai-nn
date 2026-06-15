"""Developmental soak restart drills: graceful, crash marker, recovery, no kill."""

from __future__ import annotations

import inspect

from solaris_ai_nn.developmental_soak import (
    CheckpointManager,
    RestartDrill,
    RestartDrillRunner,
    RestartDrillType,
)
from solaris_ai_nn.developmental_soak import restart_drills


def _cm(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path), persist=False)
    cm.create(tick=0)
    return cm


def test_graceful_restart_drill_simulated(tmp_path):
    cm = _cm(tmp_path)
    runner = RestartDrillRunner()
    result = runner.run(RestartDrill(RestartDrillType.GRACEFUL_SHUTDOWN_RESTART),
                        checkpoint_manager=cm)
    assert result.outcome == "ok"
    assert result.recovery is not None


def test_crash_marker_recorded(tmp_path):
    cm = _cm(tmp_path)
    runner = RestartDrillRunner()
    result = runner.run(RestartDrill(RestartDrillType.SIMULATED_CRASH_MARKER),
                        checkpoint_manager=cm)
    assert result.crash_marker_recorded is True
    assert any(b["kind"] == "simulated_crash_marker" for b in cm.break_history)


def test_recovery_assessment_generated(tmp_path):
    cm = _cm(tmp_path)
    runner = RestartDrillRunner()
    result = runner.run(
        RestartDrill(RestartDrillType.STATE_CONTINUITY_VERIFICATION),
        checkpoint_manager=cm)
    rec = result.recovery.to_dict()
    assert "continuity_preserved" in rec
    # Gaps are operational, not biological.
    assert rec["biological"] is False


def test_corruption_detection_drill(tmp_path):
    cm = _cm(tmp_path)
    runner = RestartDrillRunner()
    result = runner.run(
        RestartDrill(RestartDrillType.CHECKPOINT_CORRUPTION_DETECTION),
        checkpoint_manager=cm)
    assert result.outcome in ("detected", "no_checkpoint")


def test_no_process_kill_in_source():
    src = inspect.getsource(restart_drills)
    assert "os.kill" not in src
    assert "sys.exit" not in src
    assert "SIGKILL" not in src
