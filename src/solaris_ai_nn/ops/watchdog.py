"""Watchdog -- notices trouble and *requests* a safe stop. Never kills.

The watchdog observes heartbeat/checkpoint freshness, run duration, health
levels, artifact growth, and repeated failures, and returns decisions:
``continue`` / ``checkpoint_now`` / ``warn`` / ``safe_shutdown`` /
``emergency_stop_requested``. It has no power of its own: the supervisor acts
on its decisions, and even an emergency stop attempts a final checkpoint.
The watchdog never touches the process: it only returns decisions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

CONTINUE = "continue"
CHECKPOINT_NOW = "checkpoint_now"
WARN = "warn"
SAFE_SHUTDOWN = "safe_shutdown"
EMERGENCY_STOP = "emergency_stop_requested"

DECISIONS = (CONTINUE, CHECKPOINT_NOW, WARN, SAFE_SHUTDOWN, EMERGENCY_STOP)


@dataclass
class WatchdogDecision:
    decision: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"decision": self.decision, "reason": self.reason}


@dataclass
class Watchdog:
    """Threshold-based supervisor advisor."""

    heartbeat_stale_s: float = 60.0
    checkpoint_stale_s: float = 120.0
    max_duration_s: Optional[float] = None
    max_artifact_bytes: int = 200 * 1024 * 1024
    critical_strikes: int = 2
    failure_strikes: int = 3

    _consecutive_critical: int = field(default=0, init=False)
    _consecutive_failures: int = field(default=0, init=False)
    _stop_requested: bool = field(default=False, init=False)
    _stop_reason: Optional[str] = field(default=None, init=False)
    _decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _started_at: float = field(default_factory=time.time, init=False)

    def tick(self, snapshot: Dict[str, Any]) -> WatchdogDecision:
        """Evaluate one supervision snapshot; returns the decision."""
        now = snapshot.get("now", time.time())
        decision = WatchdogDecision(CONTINUE)

        # Repeated experiment/segment failures escalate fastest.
        if snapshot.get("segment_failed"):
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0
        if self._consecutive_failures >= self.failure_strikes:
            decision = WatchdogDecision(
                EMERGENCY_STOP,
                f"{self._consecutive_failures} consecutive segment failures")

        # Health escalation: one critical warns; repeated criticals stop.
        health = snapshot.get("health_level", "ok")
        if health == "critical":
            self._consecutive_critical += 1
            if self._consecutive_critical >= self.critical_strikes:
                decision = WatchdogDecision(
                    SAFE_SHUTDOWN,
                    f"health critical for {self._consecutive_critical} "
                    "consecutive checks")
            elif decision.decision == CONTINUE:
                decision = WatchdogDecision(WARN, "health critical (strike 1)")
        else:
            self._consecutive_critical = 0
            if health == "warning" and decision.decision == CONTINUE:
                decision = WatchdogDecision(WARN, "health warning")

        # Duration bound.
        started = snapshot.get("started_at", self._started_at)
        if self.max_duration_s is not None \
                and now - started >= self.max_duration_s \
                and decision.decision not in (SAFE_SHUTDOWN, EMERGENCY_STOP):
            decision = WatchdogDecision(
                SAFE_SHUTDOWN,
                f"run duration {now - started:.1f}s reached the "
                f"{self.max_duration_s}s bound")

        # Artifact growth.
        artifact_bytes = int(snapshot.get("artifact_bytes", 0))
        if artifact_bytes > self.max_artifact_bytes \
                and decision.decision not in (SAFE_SHUTDOWN, EMERGENCY_STOP):
            decision = WatchdogDecision(
                SAFE_SHUTDOWN,
                f"artifact growth {artifact_bytes} bytes exceeds budget")

        # Staleness: heartbeat critical (stuck loop), checkpoint -> request one.
        hb = float(snapshot.get("last_heartbeat_ts", 0.0) or 0.0)
        if hb > 0 and now - hb > self.heartbeat_stale_s \
                and decision.decision not in (SAFE_SHUTDOWN, EMERGENCY_STOP):
            decision = WatchdogDecision(
                SAFE_SHUTDOWN,
                f"heartbeat stale for {now - hb:.1f}s (possible stuck loop)")
        cp = float(snapshot.get("last_checkpoint_ts", 0.0) or 0.0)
        if cp > 0 and now - cp > self.checkpoint_stale_s \
                and decision.decision == CONTINUE:
            decision = WatchdogDecision(
                CHECKPOINT_NOW,
                f"checkpoint age {now - cp:.1f}s exceeds "
                f"{self.checkpoint_stale_s}s")

        if decision.decision in (SAFE_SHUTDOWN, EMERGENCY_STOP):
            self._stop_requested = True
            self._stop_reason = decision.reason
        self._decisions.append({"ts": now, **decision.to_dict()})
        self._decisions = self._decisions[-100:]
        return decision

    def should_stop(self) -> bool:
        return self._stop_requested

    def reason(self) -> Optional[str]:
        return self._stop_reason

    def snapshot(self) -> Dict[str, Any]:
        return {
            "stop_requested": self._stop_requested,
            "stop_reason": self._stop_reason,
            "consecutive_critical": self._consecutive_critical,
            "consecutive_failures": self._consecutive_failures,
            "recent_decisions": self._decisions[-5:],
            "thresholds": {
                "heartbeat_stale_s": self.heartbeat_stale_s,
                "checkpoint_stale_s": self.checkpoint_stale_s,
                "max_duration_s": self.max_duration_s,
                "max_artifact_bytes": self.max_artifact_bytes,
            },
        }
