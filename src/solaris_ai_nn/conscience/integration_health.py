"""Integration health -- is the assembled organism actually wired correctly?

The :class:`IntegrationHealthMonitor` inspects a live (or just-initialized)
:class:`ConscienceOrchestrator` and reports whether the spine, bus, module
registry, lifecycle, scheduler, and critical modules are healthy. It answers
"is the whole thing connected, or only some parts?" without ever actuating
anything -- it is a read-only inspector.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class HealthStatus:
    HEALTHY = "healthy"
    PARTIAL = "partial"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

    ALL = (HEALTHY, PARTIAL, DEGRADED, FAILED, UNKNOWN)
    # Worst-to-best ordering for aggregation.
    _RANK = {UNKNOWN: 0, HEALTHY: 1, PARTIAL: 2, DEGRADED: 3, FAILED: 4}

    @classmethod
    def worst(cls, statuses: List[str]) -> str:
        if not statuses:
            return cls.UNKNOWN
        return max(statuses, key=lambda s: cls._RANK.get(s, 0))


@dataclass
class IntegrationHealthCheck:
    """One named check with a status and human-readable detail."""

    name: str
    status: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "status": self.status,
                "detail": self.detail}


@dataclass
class IntegrationHealthReport:
    """The aggregate health of an assembled runtime."""

    overall: str = HealthStatus.UNKNOWN
    checks: List[IntegrationHealthCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def healthy(self) -> bool:
        return self.overall in (HealthStatus.HEALTHY, HealthStatus.PARTIAL)

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append(IntegrationHealthCheck(name, status, detail))
        if status in (HealthStatus.DEGRADED, HealthStatus.FAILED):
            self.warnings.append(f"{name}: {detail or status}")

    def finalize(self) -> "IntegrationHealthReport":
        self.overall = HealthStatus.worst([c.status for c in self.checks])
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "healthy": self.healthy,
            "checks": [c.to_dict() for c in self.checks],
            "warnings": list(self.warnings),
            "timestamp": self.timestamp,
        }


@dataclass
class IntegrationHealthMonitor:
    """Inspects an orchestrator and reports integration health (read-only)."""

    history: List[IntegrationHealthReport] = field(default_factory=list,
                                                  init=False)

    def check(self, orchestrator: Any) -> IntegrationHealthReport:
        report = IntegrationHealthReport()
        self._check_spine(orchestrator, report)
        self._check_bus(orchestrator, report)
        self._check_registry(orchestrator, report)
        self._check_lifecycle(orchestrator, report)
        self._check_scheduler(orchestrator, report)
        self._check_safety(orchestrator, report)
        report.finalize()
        self.history.append(report)
        self.history = self.history[-200:]
        return report

    # -- individual checks --------------------------------------------------------

    def _check_spine(self, orch: Any, report: IntegrationHealthReport) -> None:
        spine = getattr(orch, "spine", None)
        if spine is None:
            report.add("spine", HealthStatus.UNKNOWN, "no spine")
            return
        counts = spine.trace.status_counts
        degraded = counts.get("degraded", 0)
        ran = counts.get("ran", 0)
        if degraded and ran and degraded > ran:
            report.add("spine", HealthStatus.DEGRADED,
                       f"{degraded} degraded vs {ran} ran")
        elif degraded:
            report.add("spine", HealthStatus.PARTIAL,
                       f"{degraded} phase(s) degraded")
        elif ran:
            report.add("spine", HealthStatus.HEALTHY, f"{ran} phases ran")
        else:
            report.add("spine", HealthStatus.UNKNOWN, "spine has not run")

    def _check_bus(self, orch: Any, report: IntegrationHealthReport) -> None:
        bus = getattr(orch, "bus", None)
        if bus is None:
            report.add("bus", HealthStatus.UNKNOWN, "no bus")
            return
        report.add("bus", HealthStatus.HEALTHY,
                   f"{bus.message_count()} messages")

    def _check_registry(self, orch: Any,
                        report: IntegrationHealthReport) -> None:
        registry = getattr(orch, "registry", None)
        if registry is None:
            report.add("registry", HealthStatus.UNKNOWN, "no registry")
            return
        missing = registry.missing()
        unmet = registry.validate_dependencies()
        # A missing *critical* module is a failure.
        critical_missing = [m for m in missing
                            if registry.modules.get(m)
                            and registry.modules[m].critical]
        if critical_missing:
            report.add("registry", HealthStatus.FAILED,
                       f"critical module(s) unavailable: "
                       f"{', '.join(critical_missing)}")
        elif missing:
            report.add("registry", HealthStatus.PARTIAL,
                       f"enabled-but-unavailable: {', '.join(missing)}")
        elif unmet:
            report.add("registry", HealthStatus.PARTIAL,
                       f"unmet dependencies: {sorted(unmet)}")
        else:
            report.add("registry", HealthStatus.HEALTHY,
                       f"{len(registry.enabled())} modules enabled")

    def _check_lifecycle(self, orch: Any,
                        report: IntegrationHealthReport) -> None:
        lifecycle = getattr(orch, "lifecycle", None)
        if lifecycle is None:
            report.add("lifecycle", HealthStatus.UNKNOWN, "no lifecycle")
            return
        failed = lifecycle.failed()
        degraded = lifecycle.degraded()
        if failed:
            report.add("lifecycle", HealthStatus.FAILED,
                       f"failed: {', '.join(failed)}")
        elif degraded:
            report.add("lifecycle", HealthStatus.DEGRADED,
                       f"degraded: {', '.join(degraded)}")
        else:
            report.add("lifecycle", HealthStatus.HEALTHY,
                       f"{len(lifecycle.running())} running")

    def _check_scheduler(self, orch: Any,
                        report: IntegrationHealthReport) -> None:
        scheduler = getattr(orch, "scheduler", None)
        if scheduler is None:
            report.add("scheduler", HealthStatus.UNKNOWN, "no scheduler")
            return
        report.add("scheduler", HealthStatus.HEALTHY,
                   f"{len(scheduler.slots)} slots, "
                   f"{scheduler.skip_count} cadence skips")

    def _check_safety(self, orch: Any,
                     report: IntegrationHealthReport) -> None:
        safety = getattr(orch, "safety", None)
        if safety is None:
            report.add("safety", HealthStatus.UNKNOWN, "no safety validator")
            return
        if safety.can_act_in_real_world() or safety.can_network() \
                or safety.can_modify_source():
            report.add("safety", HealthStatus.FAILED,
                       "safety invariants violated")
        else:
            report.add("safety", HealthStatus.HEALTHY,
                       f"{safety.rejected_count} rejections; invariants hold")

    def snapshot(self) -> Dict[str, Any]:
        latest = self.history[-1].to_dict() if self.history else None
        return {"check_count": len(self.history), "latest": latest}
