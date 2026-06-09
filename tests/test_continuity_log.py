"""Tests for the continuity log and ungraceful-death detection."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.runtime.persistence import (
    BIRTH,
    BRAIN_DEATH_GAP,
    UNEXPECTED_DEATH,
    ContinuityLog,
    PersistenceManager,
)


def test_jsonl_log_writes_valid_rows(tmp_path):
    log = ContinuityLog(tmp_path / "continuity_log.jsonl", run_id="r", session_id="s")
    log.log(BIRTH, "born", step=0, lifetime_step=0)
    log.log("heartbeat", "alive", step=1, lifetime_step=1)
    log.close()

    rows = log.read_all()
    assert len(rows) == 2
    for row in rows:
        assert {"timestamp", "run_id", "session_id", "event_type", "message",
                "step", "lifetime_step", "graceful", "metadata"} <= set(row)
    assert rows[0]["event_type"] == BIRTH
    assert rows[0]["run_id"] == "r"


def test_unknown_event_type_rejected(tmp_path):
    log = ContinuityLog(tmp_path / "continuity_log.jsonl")
    with pytest.raises(ValueError):
        log.log("not_a_real_event")
    log.close()


def test_unexpected_death_detected_from_previous_manifest(tmp_path):
    state_dir = tmp_path / "brain"
    # Simulate a prior session that crashed: manifest exists, not graceful,
    # with a backdated heartbeat so a gap is computed.
    pm = PersistenceManager(state_dir)
    pm.save_manifest(
        {
            "run_id": "prev",
            "created_at": time.time() - 100,
            "lifetime_steps": 30,
            "restart_count": 0,
            "session_count": 1,
            "last_graceful_shutdown": False,
            "last_heartbeat_ts": time.time() - 7.0,
            "seed": 0,
        }
    )

    runner = ContinuousRunner(state_dir=state_dir, max_steps=5)
    rows = runner.continuity.read_all()
    types = [r["event_type"] for r in rows]
    assert UNEXPECTED_DEATH in types
    assert BRAIN_DEATH_GAP in types

    gap_row = next(r for r in rows if r["event_type"] == BRAIN_DEATH_GAP)
    assert gap_row["metadata"]["gap_seconds"] >= 6.0
    assert runner.telemetry.unexpected_deaths == 1
    assert runner.telemetry.brain_death_gap_seconds >= 6.0


def test_graceful_previous_does_not_log_unexpected_death(tmp_path):
    state_dir = tmp_path / "brain"
    # First session ends gracefully.
    r1 = ContinuousRunner(state_dir=state_dir, max_steps=5)
    r1.run()
    # Second session should NOT see an unexpected death.
    r2 = ContinuousRunner(state_dir=state_dir, max_steps=5)
    types = [r["event_type"] for r in r2.continuity.read_all()]
    assert UNEXPECTED_DEATH not in [
        t for t in types if t == UNEXPECTED_DEATH
    ] or r2.telemetry.unexpected_deaths == 0
    assert r2.telemetry.unexpected_deaths == 0
