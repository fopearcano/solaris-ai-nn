"""Pilot-1 resource budget -- stdlib-only disk/usage tracking and projection.

The :class:`ResourceBudgetMonitor` scans the pilot directories with the
standard library (no ``psutil``), estimates current and projected disk use
(30/90/365 days), and raises a warning when a projection exceeds the budget.
CPU/memory are reported as hints/unknown when no reliable stdlib value exists.
A warning may request auto-regeneration log rotation / compaction.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _dir_bytes(path: Optional[str]) -> int:
    if not path or not os.path.isdir(path):
        return 0
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total


def _memory_hint_mb() -> Optional[float]:
    """Best-effort RSS in MB using only the stdlib; None if unavailable."""
    try:
        import resource  # POSIX-only stdlib

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss is KB on Linux, bytes on macOS.
        return round(rss / 1024.0, 2)
    except Exception:
        return None


@dataclass
class ResourceBudget:
    """The disk/memory limits a pilot must respect."""

    max_disk_mb: float = 2048.0
    max_memory_mb: float = 1024.0
    max_cpu_percent_hint: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ResourceBudgetEstimate:
    """A point-in-time usage measurement plus projections."""

    state_bytes: int = 0
    artifact_bytes: int = 0
    log_bytes: int = 0
    report_bytes: int = 0
    total_bytes: int = 0
    memory_hint_mb: Optional[float] = None
    event_rate_per_hour: float = 0.0
    telemetry_rate_per_hour: float = 0.0
    checkpoint_bytes: int = 0
    compression_ratio: float = 1.0
    elapsed_days: float = 0.0
    projected_30d_mb: float = 0.0
    projected_90d_mb: float = 0.0
    projected_365d_mb: float = 0.0
    over_budget: bool = False
    warnings: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def total_mb(self) -> float:
        return round(self.total_bytes / (1024 * 1024), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "total_mb": self.total_mb}


@dataclass
class ResourceBudgetMonitor:
    """Scans pilot directories and projects future disk use (stdlib only)."""

    budget: ResourceBudget = field(default_factory=ResourceBudget)
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    log_dir: Optional[str] = None
    report_dir: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    history: List[ResourceBudgetEstimate] = field(default_factory=list,
                                                  init=False)

    def estimate(self, event_count: int = 0, telemetry_count: int = 0,
                 checkpoint_bytes: int = 0,
                 compression_ratio: float = 1.0) -> ResourceBudgetEstimate:
        state = _dir_bytes(self.state_dir)
        artifact = _dir_bytes(self.artifact_dir)
        log = _dir_bytes(self.log_dir)
        report = _dir_bytes(self.report_dir)
        total = state + artifact + log + report
        elapsed_s = max(1.0, time.time() - self.started_at)
        elapsed_days = elapsed_s / 86400.0
        elapsed_hours = elapsed_s / 3600.0
        # Project linearly off the current per-day growth; floor at a tiny
        # elapsed window so projections are meaningful even early on.
        mb = total / (1024 * 1024)
        per_day_mb = mb / max(elapsed_days, 1.0 / 24.0)
        est = ResourceBudgetEstimate(
            state_bytes=state, artifact_bytes=artifact, log_bytes=log,
            report_bytes=report, total_bytes=total,
            memory_hint_mb=_memory_hint_mb(),
            event_rate_per_hour=round(event_count / elapsed_hours, 3),
            telemetry_rate_per_hour=round(telemetry_count / elapsed_hours, 3),
            checkpoint_bytes=checkpoint_bytes,
            compression_ratio=compression_ratio,
            elapsed_days=round(elapsed_days, 4),
            projected_30d_mb=round(per_day_mb * 30, 3),
            projected_90d_mb=round(per_day_mb * 90, 3),
            projected_365d_mb=round(per_day_mb * 365, 3))
        self._assess(est)
        self.history.append(est)
        self.history = self.history[-500:]
        return est

    def _assess(self, est: ResourceBudgetEstimate) -> None:
        if est.total_mb > self.budget.max_disk_mb:
            est.over_budget = True
            est.warnings.append(
                f"current disk use {est.total_mb} MB exceeds budget "
                f"{self.budget.max_disk_mb} MB")
        if est.projected_30d_mb > self.budget.max_disk_mb:
            est.warnings.append(
                f"projected 30-day disk use {est.projected_30d_mb} MB exceeds "
                f"budget {self.budget.max_disk_mb} MB; "
                "request log rotation / compaction")
        if est.memory_hint_mb is not None \
                and est.memory_hint_mb > self.budget.max_memory_mb:
            est.warnings.append(
                f"memory hint {est.memory_hint_mb} MB exceeds budget "
                f"{self.budget.max_memory_mb} MB")

    def requests_hygiene(self, est: Optional[ResourceBudgetEstimate] = None,
                         ) -> bool:
        """Does the latest estimate justify an auto-regeneration hygiene pass?"""
        est = est or (self.history[-1] if self.history else None)
        return bool(est and (est.over_budget or est.warnings))

    def hygiene_request(self, est: Optional[ResourceBudgetEstimate] = None,
                        ) -> Optional[Dict[str, Any]]:
        """A context dict auto-regeneration can act on (rotation/compaction)."""
        if not self.requests_hygiene(est):
            return None
        return {"memory_bloat": True, "log_rotation_requested": True,
                "reason": "pilot resource budget warning"}

    def snapshot(self) -> Dict[str, Any]:
        latest = self.history[-1].to_dict() if self.history else None
        return {"budget": self.budget.to_dict(), "latest": latest,
                "estimate_count": len(self.history),
                "requests_hygiene": self.requests_hygiene()}
