"""Pilot-1 observability -- a low-overhead, append-only metric stream.

The :class:`PilotObservabilityCollector` records heartbeat, uptime, restart,
checkpoint, spine/bus, module-health, growth, and safety/governance counts to
an append-only JSONL stream that survives restarts. It never logs secrets and
never hides safety events; it computes a small set of derived signals
(structural-change score, stagnation duration, drift velocity) for the
dashboards and reviews.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ObservationEvent:
    """One low-overhead observation sample."""

    kind: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"OBS_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "kind": self.kind,
                "timestamp": self.timestamp, "payload": self.payload}


@dataclass
class ObservationStream:
    """An append-only JSONL stream of observation events (restart-safe)."""

    path: str
    count: int = field(default=0, init=False)

    def append(self, event: ObservationEvent) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        self.count += 1

    def read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        out: List[Dict[str, Any]] = []
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        return out


# The canonical metric keys an observation snapshot carries.
METRIC_KEYS = (
    "uptime_seconds", "restart_count", "checkpoint_success",
    "checkpoint_failure", "spine_phase_count", "bus_message_count",
    "degraded_module_count", "memory_size_bytes", "artifact_size_bytes",
    "ecology_event_count", "proto_symbol_count",
    "active_perception_sampling_count", "hypothesis_count",
    "logos_tension_count", "autoregeneration_degradation_count",
    "safety_incident_count", "governance_block_count",
    "structural_change_score", "stagnation_seconds", "drift_velocity",
)


@dataclass
class PilotObservabilityCollector:
    """Collects, derives, and persists pilot observability metrics."""

    base_dir: str = ".solaris_ai_nn_pilot1"
    started_at: float = field(default_factory=time.time)
    restart_count: int = 0
    _latest: Dict[str, Any] = field(default_factory=dict, init=False)
    _prev_structural: Optional[float] = field(default=None, init=False)
    _last_change_ts: float = field(default_factory=time.time, init=False)

    def __post_init__(self) -> None:
        self.obs_path = os.path.join(self.base_dir, "observability.jsonl")
        self.daily_path = os.path.join(self.base_dir, "metrics_daily.jsonl")
        self.incidents_path = os.path.join(self.base_dir, "incidents.jsonl")
        self.stream = ObservationStream(self.obs_path)

    # -- recording --------------------------------------------------------------

    def heartbeat(self, extra: Optional[Dict[str, Any]] = None) -> ObservationEvent:
        event = ObservationEvent(kind="heartbeat", payload={
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "restart_count": self.restart_count, **(extra or {})})
        self.stream.append(event)
        return event

    def record_incident(self, incident_type: str, severity: str,
                        message: str) -> ObservationEvent:
        """Safety/ops incidents are never hidden; they go to their own log."""
        event = ObservationEvent(kind="incident", payload={
            "type": incident_type, "severity": severity, "message": message})
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.incidents_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        self.stream.append(event)
        return event

    def observe(self, orchestrator: Any = None,
                snapshot: Optional[Dict[str, Any]] = None,
                ) -> Dict[str, Any]:
        """Collect one observation from an orchestrator (or a raw snapshot)."""
        metrics = self._extract(orchestrator, snapshot or {})
        metrics["uptime_seconds"] = round(time.time() - self.started_at, 3)
        metrics["restart_count"] = self.restart_count
        # Derived: structural-change score, stagnation, drift velocity.
        score = float(metrics.get("structural_change_score", 0.0) or 0.0)
        now = time.time()
        if self._prev_structural is not None:
            delta = abs(score - self._prev_structural)
            metrics["drift_velocity"] = round(delta, 6)
            if delta > 1e-6:
                self._last_change_ts = now
        else:
            metrics["drift_velocity"] = 0.0
        metrics["stagnation_seconds"] = round(now - self._last_change_ts, 3)
        self._prev_structural = score
        self._latest = metrics
        self.stream.append(ObservationEvent(kind="metrics", payload=metrics))
        return metrics

    def _extract(self, orchestrator: Any,
                 snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Pull canonical metrics from an orchestrator summary/snapshot."""
        summary: Dict[str, Any] = dict(snapshot)
        snap: Dict[str, Any] = {}
        if orchestrator is not None:
            try:
                summary = {**orchestrator.summary(), **summary}
            except Exception:
                pass
            try:
                snap = orchestrator.snapshot()
            except Exception:
                snap = {}
        spine = (snap.get("spine") or {})
        status_counts = spine.get("status_counts") or {}
        counts = summary.get("counts") or {}
        m = {k: 0 for k in METRIC_KEYS}
        m["spine_phase_count"] = int(sum(counts.values())) if counts \
            else int(status_counts.get("ran", 0) or 0)
        m["bus_message_count"] = int(summary.get("bus_message_count", 0) or 0)
        m["degraded_module_count"] = len(summary.get("degraded_modules") or [])
        safety = snap.get("safety") or {}
        m["safety_incident_count"] = int(safety.get("rejected_count", 0) or 0)
        # Optional component-derived counts, defensive across configs.
        for key, src in (("proto_symbol_count", "proto_symbol_count"),
                         ("ecology_event_count", "ecology_event_count"),
                         ("hypothesis_count", "hypothesis_count"),
                         ("logos_tension_count", "logos_tension_count"),
                         ("active_perception_sampling_count",
                          "active_perception_sampling_count"),
                         ("autoregeneration_degradation_count",
                          "autoregeneration_degradation_count"),
                         ("governance_block_count", "governance_block_count"),
                         ("structural_change_score", "structural_change_score"),
                         ("memory_size_bytes", "memory_size_bytes"),
                         ("artifact_size_bytes", "artifact_size_bytes"),
                         ("checkpoint_success", "checkpoint_success"),
                         ("checkpoint_failure", "checkpoint_failure")):
            if src in summary:
                m[key] = summary[src]
        return m

    def write_daily_rollup(self, day_number: int,
                           extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rollup = {"day": day_number, "timestamp": time.time(),
                  **self._latest, **(extra or {})}
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.daily_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rollup, default=str) + "\n")
        return rollup

    # -- views ------------------------------------------------------------------

    @property
    def latest(self) -> Dict[str, Any]:
        return dict(self._latest)

    def uptime_seconds(self) -> float:
        return round(time.time() - self.started_at, 3)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "observability_path": self.obs_path,
            "daily_path": self.daily_path,
            "incidents_path": self.incidents_path,
            "event_count": self.stream.count,
            "uptime_seconds": self.uptime_seconds(),
            "restart_count": self.restart_count,
            "latest": self.latest,
        }
