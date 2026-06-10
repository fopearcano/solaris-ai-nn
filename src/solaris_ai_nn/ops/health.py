"""Health checks -- is the long-running system actually okay right now?

The :class:`HealthMonitor` inspects a status snapshot (plain dicts: lifecycle,
telemetry, substrate, persistence paths, memory, plasticity, embodiment,
language) and produces a :class:`HealthReport` of domain checks at four levels:
``ok`` / ``warning`` / ``critical`` / ``unknown``. The monitor is stateful only
to detect "stopped increasing" between consecutive checks.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

OK, WARNING, CRITICAL, UNKNOWN = "ok", "warning", "critical", "unknown"
_RANK = {OK: 0, UNKNOWN: 0, WARNING: 1, CRITICAL: 2}


class HealthStatus:
    OK, WARNING, CRITICAL, UNKNOWN = OK, WARNING, CRITICAL, UNKNOWN


@dataclass
class HealthCheck:
    name: str
    domain: str
    status: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class HealthReport:
    checks: List[HealthCheck] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def level(self) -> str:
        worst = OK
        for c in self.checks:
            if _RANK.get(c.status, 0) > _RANK[worst]:
                worst = c.status
        return worst

    def issues(self) -> List[HealthCheck]:
        return [c for c in self.checks if c.status in (WARNING, CRITICAL)]

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "level": self.level,
                "checks": [c.to_dict() for c in self.checks],
                "issues": len(self.issues())}

    def to_markdown(self) -> str:
        lines = [f"## Health report — level: {self.level}", ""]
        for c in self.checks:
            lines.append(f"- [{c.status}] **{c.domain}/{c.name}**: {c.detail}")
        return "\n".join(lines)


@dataclass
class HealthMonitor:
    """Stateful domain checker over operational snapshots."""

    heartbeat_stale_s: float = 30.0
    checkpoint_stale_s: float = 300.0
    max_state_norm: float = 100.0
    inert_min_updates: int = 50
    max_trace_events: int = 50_000
    max_language_atoms: int = 50_000
    max_blocked_ratio: float = 0.6
    max_rejected_rate: float = 0.95

    _prev_counters: Dict[str, int] = field(default_factory=dict, init=False)

    def check(self, snapshot: Dict[str, Any],
              artifacts: Optional[Dict[str, str]] = None) -> HealthReport:
        report = HealthReport()
        now = snapshot.get("now", time.time())

        def add(domain: str, name: str, status: str, detail: str) -> None:
            report.checks.append(HealthCheck(name=name, domain=domain,
                                             status=status, detail=detail))

        # A. Lifecycle.
        lifecycle = snapshot.get("lifecycle")
        if lifecycle is None:
            add("lifecycle", "presence", UNKNOWN, "no lifecycle data")
        else:
            alive = lifecycle.get("alive", lifecycle.get("state") not in
                                  ("dying", "dead"))
            add("lifecycle", "alive", OK if alive else WARNING,
                f"state={lifecycle.get('state', 'unknown')}")
            hb = float(lifecycle.get("last_heartbeat_ts", 0.0) or 0.0)
            if hb > 0:
                age = now - hb
                add("lifecycle", "heartbeat_freshness",
                    OK if age <= self.heartbeat_stale_s else WARNING,
                    f"last heartbeat {age:.1f}s ago "
                    f"(threshold {self.heartbeat_stale_s}s)")
            cp = float(lifecycle.get("last_checkpoint_ts", 0.0) or 0.0)
            if cp > 0:
                age = now - cp
                add("lifecycle", "checkpoint_age",
                    OK if age <= self.checkpoint_stale_s else WARNING,
                    f"last checkpoint {age:.1f}s ago "
                    f"(threshold {self.checkpoint_stale_s}s)")

        # B. Telemetry: counters must keep increasing between checks.
        telemetry = snapshot.get("telemetry")
        if telemetry is None:
            add("telemetry", "presence", UNKNOWN, "no telemetry data")
        else:
            for counter in ("events", "reservoir_updates", "trace_event_count"):
                current = int(telemetry.get(counter, 0))
                previous = self._prev_counters.get(counter)
                if previous is not None and current <= previous \
                        and snapshot.get("expect_progress", True):
                    add("telemetry", f"{counter}_increasing", WARNING,
                        f"{counter} frozen at {current} since last check")
                else:
                    add("telemetry", f"{counter}_increasing", OK,
                        f"{counter}={current}")
                self._prev_counters[counter] = current

        # C. Substrate.
        substrate = snapshot.get("substrate")
        if substrate is None:
            add("substrate", "presence", UNKNOWN, "no substrate data")
        else:
            norm = substrate.get("state_norm", 0.0)
            if norm is None or not math.isfinite(float(norm)):
                add("substrate", "state_finite", CRITICAL,
                    f"state norm is not finite: {norm}")
            elif float(norm) > self.max_state_norm:
                add("substrate", "runaway_activity", CRITICAL,
                    f"state norm {float(norm):.1f} exceeds "
                    f"{self.max_state_norm}")
            else:
                add("substrate", "state_finite", OK,
                    f"state norm {float(norm):.4f}")
                updates = int((telemetry or {}).get("reservoir_updates", 0))
                drift = float(substrate.get("drift", substrate.get(
                    "state_drift", 0.0)) or 0.0)
                if updates >= self.inert_min_updates and float(norm) == 0.0 \
                        and drift == 0.0 and not snapshot.get("inert_expected"):
                    add("substrate", "inactivity", WARNING,
                        f"substrate inert after {updates} updates")

        # D. Persistence.
        state_dir = snapshot.get("state_dir")
        if state_dir:
            path = Path(state_dir)
            writable = path.exists() and os.access(path, os.W_OK)
            add("persistence", "state_dir_writable",
                OK if writable else CRITICAL, str(path))
            checkpoint = path / "latest_checkpoint.json"
            add("persistence", "checkpoint_present",
                OK if checkpoint.exists() else WARNING,
                str(checkpoint) + ("" if checkpoint.exists() else " missing"))
        artifact_dir = snapshot.get("artifact_dir")
        if artifact_dir:
            path = Path(artifact_dir)
            path.mkdir(parents=True, exist_ok=True)
            add("persistence", "artifact_dir_writable",
                OK if os.access(path, os.W_OK) else CRITICAL, str(path))

        # E. Memory.
        if telemetry is not None:
            trace_len = int(telemetry.get("memory_trace_length", 0))
            add("memory", "trace_bounded",
                OK if trace_len <= self.max_trace_events else WARNING,
                f"trace length {trace_len} (bound {self.max_trace_events})")

        # F. Plasticity.
        plasticity = snapshot.get("plasticity")
        if plasticity:
            rollback = plasticity.get("rollback", {}) or {}
            failures = int(plasticity.get("rollback_failures", 0))
            add("plasticity", "rollback_failures",
                OK if failures == 0 else WARNING,
                f"{failures} rollback failures")
            applied = int(plasticity.get("applied_count", 0))
            rejected = int(plasticity.get("rejected_count", 0))
            total = applied + rejected
            rate = (rejected / total) if total else 0.0
            add("plasticity", "rejection_rate",
                OK if rate <= self.max_rejected_rate or total < 5 else WARNING,
                f"{rejected}/{total} proposals rejected")

        # G. Embodiment.
        embodiment = snapshot.get("embodiment")
        if embodiment:
            executed = int(embodiment.get("actions_executed",
                                          embodiment.get("executed_actions", 0)))
            blocked = int(embodiment.get("actions_blocked",
                                         embodiment.get("blocked_actions", 0)))
            total = executed + blocked
            ratio = (blocked / total) if total else 0.0
            add("embodiment", "blocked_ratio",
                OK if ratio <= self.max_blocked_ratio else WARNING,
                f"{blocked}/{total} actions blocked")
            energy = embodiment.get("energy")
            if isinstance(energy, dict):
                energy = energy.get("energy")
            if energy is not None and not math.isfinite(float(energy)):
                add("embodiment", "body_finite", CRITICAL,
                    f"energy not finite: {energy}")
            elif embodiment.get("exhausted") and executed == 0 and total > 10:
                add("embodiment", "permanently_exhausted", WARNING,
                    "body exhausted with no executed actions")

        # H. Language.
        language = snapshot.get("language")
        if language:
            atoms = int(language.get("meaning_atoms",
                                     language.get("meaning_atom_count", 0)))
            add("language", "trace_bounded",
                OK if atoms <= self.max_language_atoms else WARNING,
                f"{atoms} meaning atoms (bound {self.max_language_atoms})")

        return report
