"""Tests for the runtime lifecycle state machine."""

from __future__ import annotations

import time

from solaris_ai_nn.runtime.lifecycle import (
    BORN,
    DEAD,
    RUNNING,
    SLEEPING,
    RuntimeLifecycle,
)
from solaris_ai_nn.runtime.persistence import GRACEFUL_DEATH, PersistenceManager


def test_initial_state_is_born():
    lc = RuntimeLifecycle(run_id="r", session_id="s")
    assert lc.state == BORN
    assert lc.is_alive()


def test_birth_running_death_states():
    lc = RuntimeLifecycle(run_id="r", session_id="s")
    lc.birth()
    assert lc.state == RUNNING
    lc.sleep("silence")
    assert lc.state == SLEEPING
    lc.wake("stimulus")
    assert lc.state == RUNNING
    lc.die("done", graceful=True)
    assert lc.state == DEAD
    assert not lc.is_alive()


def test_heartbeat_updates_timestamp():
    lc = RuntimeLifecycle(run_id="r", session_id="s")
    lc.birth()
    before = lc.last_heartbeat_ts
    time.sleep(0.01)
    lc.heartbeat(step=5)
    assert lc.last_heartbeat_ts >= before
    assert lc.last_heartbeat_step == 5


def test_graceful_death_is_recorded(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    clog = pm.continuity_log("r", "s")
    lc = RuntimeLifecycle(run_id="r", session_id="s", continuity_log=clog)
    lc.birth()
    lc.die("session complete", graceful=True, step=10, lifetime_step=10)
    clog.close()
    rows = clog.read_all()
    death_rows = [r for r in rows if r["event_type"] == GRACEFUL_DEATH]
    assert len(death_rows) == 1
    assert death_rows[0]["graceful"] is True
    assert lc.graceful is True


def test_snapshot_fields():
    lc = RuntimeLifecycle(run_id="r", session_id="s", is_restart=True)
    lc.birth()
    snap = lc.snapshot()
    assert snap["state"] == RUNNING
    assert snap["is_restart"] is True
    assert snap["alive"] is True
    assert "last_heartbeat_ts" in snap
