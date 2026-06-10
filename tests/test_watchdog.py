"""Tests for the Watchdog."""

from __future__ import annotations

import inspect
import time

from solaris_ai_nn.ops import watchdog as wd_mod
from solaris_ai_nn.ops.watchdog import Watchdog


def _snap(**kw):
    now = time.time()
    base = {"now": now, "started_at": now - 1, "health_level": "ok",
            "last_heartbeat_ts": now - 1, "last_checkpoint_ts": now - 1,
            "artifact_bytes": 0, "segment_failed": False}
    base.update(kw)
    return base


def test_continues_on_healthy_snapshot():
    dog = Watchdog()
    decision = dog.tick(_snap())
    assert decision.decision == "continue"
    assert not dog.should_stop()


def test_requests_checkpoint_on_stale_checkpoint():
    dog = Watchdog(checkpoint_stale_s=10.0)
    decision = dog.tick(_snap(last_checkpoint_ts=time.time() - 100))
    assert decision.decision == "checkpoint_now"
    assert not dog.should_stop()  # checkpoint request is not a stop


def test_safe_shutdown_on_repeated_critical_health():
    dog = Watchdog(critical_strikes=2)
    first = dog.tick(_snap(health_level="critical"))
    assert first.decision == "warn"
    second = dog.tick(_snap(health_level="critical"))
    assert second.decision == "safe_shutdown"
    assert dog.should_stop()
    assert "critical" in dog.reason()


def test_duration_and_growth_bounds():
    dog = Watchdog(max_duration_s=10.0)
    decision = dog.tick(_snap(started_at=time.time() - 100))
    assert decision.decision == "safe_shutdown"
    dog2 = Watchdog(max_artifact_bytes=100)
    assert dog2.tick(_snap(artifact_bytes=1000)).decision == "safe_shutdown"


def test_emergency_on_repeated_failures():
    dog = Watchdog(failure_strikes=2)
    dog.tick(_snap(segment_failed=True))
    decision = dog.tick(_snap(segment_failed=True))
    assert decision.decision == "emergency_stop_requested"


def test_watchdog_never_kills_process_directly():
    source = inspect.getsource(wd_mod)
    for forbidden in ("os._exit", "sys.exit", "os.kill", "signal.", "SIGKILL"):
        assert forbidden not in source, forbidden
    assert "snapshot" in dir(Watchdog)
