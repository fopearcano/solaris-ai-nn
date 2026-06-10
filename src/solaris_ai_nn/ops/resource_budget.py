"""ResourceBudget -- soft limits that keep long runs from eating the host.

Stdlib only: ``time``/``os``/``pathlib`` plus the optional ``resource`` module
(used for max RSS when available, silently skipped when not — e.g. Windows).
Violations are reported, never enforced here; the supervisor decides.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:  # optional, POSIX-only
    import resource as _resource
except ImportError:  # pragma: no cover - platform dependent
    _resource = None


def directory_bytes(path: Union[str, Path]) -> int:
    """Total bytes of files under ``path`` (0 if absent)."""
    base = Path(path)
    if not base.exists():
        return 0
    return sum(p.stat().st_size for p in base.rglob("*") if p.is_file())


@dataclass
class BudgetReport:
    within: bool
    violations: List[str] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ResourceBudget:
    """Soft operational limits for one supervised run."""

    max_runtime_s: Optional[float] = 24 * 3600.0
    max_steps: Optional[int] = 1_000_000
    max_trace_events: int = 100_000
    max_artifact_bytes: int = 200 * 1024 * 1024
    max_checkpoints: int = 10_000
    max_report_files: int = 1_000
    max_plasticity_mutations: int = 10_000
    max_substrate_size: int = 8192
    max_event_rate_per_s: float = 100_000.0
    max_language_atoms: int = 100_000

    _last_report: Optional[BudgetReport] = field(default=None, init=False)

    def check_budget(self, snapshot: Dict[str, Any],
                     artifact_dir: Optional[Union[str, Path]] = None) -> BudgetReport:
        violations: List[str] = []
        usage: Dict[str, Any] = {}
        telemetry = snapshot.get("telemetry", {}) or {}

        runtime = float(snapshot.get("runtime_s", 0.0))
        usage["runtime_s"] = runtime
        if self.max_runtime_s is not None and runtime > self.max_runtime_s:
            violations.append(f"runtime {runtime:.0f}s > {self.max_runtime_s}s")

        steps = int(telemetry.get("lifetime_steps", telemetry.get("steps", 0)))
        usage["steps"] = steps
        if self.max_steps is not None and steps > self.max_steps:
            violations.append(f"steps {steps} > {self.max_steps}")

        trace = int(telemetry.get("memory_trace_length", 0))
        usage["trace_events"] = trace
        if trace > self.max_trace_events:
            violations.append(f"trace events {trace} > {self.max_trace_events}")

        if artifact_dir is not None:
            size = directory_bytes(artifact_dir)
            usage["artifact_bytes"] = size
            if size > self.max_artifact_bytes:
                violations.append(
                    f"artifact bytes {size} > {self.max_artifact_bytes}")
            reports = len(list(Path(artifact_dir).rglob("*.md"))) \
                if Path(artifact_dir).exists() else 0
            usage["report_files"] = reports
            if reports > self.max_report_files:
                violations.append(f"report files {reports} > "
                                  f"{self.max_report_files}")

        checkpoints = int(telemetry.get("checkpoints", 0))
        usage["checkpoints"] = checkpoints
        if checkpoints > self.max_checkpoints:
            violations.append(f"checkpoints {checkpoints} > "
                              f"{self.max_checkpoints}")

        mutations = int((snapshot.get("plasticity") or {}).get(
            "applied_count", 0))
        usage["plasticity_mutations"] = mutations
        if mutations > self.max_plasticity_mutations:
            violations.append(f"mutations {mutations} > "
                              f"{self.max_plasticity_mutations}")

        substrate_size = int((snapshot.get("substrate") or {}).get(
            "state_size", 0))
        usage["substrate_size"] = substrate_size
        if substrate_size > self.max_substrate_size:
            violations.append(f"substrate size {substrate_size} > "
                              f"{self.max_substrate_size}")

        rate = float(telemetry.get("events_per_second", 0.0))
        usage["event_rate_per_s"] = rate
        if rate > self.max_event_rate_per_s:
            violations.append(f"event rate {rate:.0f}/s > "
                              f"{self.max_event_rate_per_s}/s")

        atoms = int((snapshot.get("language") or {}).get("meaning_atoms", 0))
        usage["language_atoms"] = atoms
        if atoms > self.max_language_atoms:
            violations.append(f"language atoms {atoms} > "
                              f"{self.max_language_atoms}")

        if _resource is not None:  # optional, informational only
            try:
                usage["max_rss_kb"] = \
                    _resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss
            except (OSError, ValueError):  # pragma: no cover
                pass

        self._last_report = BudgetReport(within=not violations,
                                         violations=violations, usage=usage)
        return self._last_report

    def within_budget(self) -> bool:
        return self._last_report is None or self._last_report.within

    def violations(self) -> List[str]:
        return [] if self._last_report is None else list(
            self._last_report.violations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "limits": {
                "max_runtime_s": self.max_runtime_s,
                "max_steps": self.max_steps,
                "max_trace_events": self.max_trace_events,
                "max_artifact_bytes": self.max_artifact_bytes,
                "max_checkpoints": self.max_checkpoints,
                "max_report_files": self.max_report_files,
                "max_plasticity_mutations": self.max_plasticity_mutations,
                "max_substrate_size": self.max_substrate_size,
                "max_event_rate_per_s": self.max_event_rate_per_s,
                "max_language_atoms": self.max_language_atoms,
            },
            "last_report": (self._last_report.to_dict()
                            if self._last_report else None),
        }
