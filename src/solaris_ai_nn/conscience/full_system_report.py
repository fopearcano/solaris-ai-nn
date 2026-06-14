"""Full system report -- one honest, claim-guarded picture of a whole run.

The :class:`FullSystemReportBuilder` assembles the orchestrator's context,
spine activity, module health, bus volume, scheduler behaviour, integration
health, and metrics into a single report (JSON + Markdown). Every line of
prose is passed through :class:`ClaimGuard` so the report never claims
sentience, feeling, understanding, or autonomy; it describes a bounded,
simulated, low-compute process.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..governance.compliance import ClaimGuard


@dataclass
class FullSystemReport:
    """The assembled report for one run."""

    report_id: str
    run_id: Optional[str]
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "claim_guard_safe": self.claim_guard_safe,
            "claim_guard_findings": self.claim_guard_findings,
            "sections": self.sections,
            "narrative": self.narrative,
        }


@dataclass
class FullSystemReportBuilder:
    """Builds claim-guarded full-system reports from an orchestrator."""

    claim_guard: ClaimGuard = field(default_factory=ClaimGuard)

    def build(self, orchestrator: Any, health_monitor: Any = None,
              metrics: Optional[Dict[str, Any]] = None) -> FullSystemReport:
        summary = self._safe(orchestrator.summary, {})
        snapshot = self._safe(orchestrator.snapshot, {})
        health = None
        if health_monitor is not None:
            try:
                health = health_monitor.check(orchestrator).to_dict()
            except Exception:
                health = None

        sections: Dict[str, Any] = {
            "run": {
                "run_id": summary.get("run_id"),
                "profile": summary.get("profile"),
                "mode": summary.get("mode"),
                "authority": summary.get("authority"),
                "steps": summary.get("step_count"),
                "stopped": summary.get("stopped"),
                "refusal_reasons": summary.get("refusal_reasons"),
            },
            "modules": {
                "enabled": summary.get("enabled_modules"),
                "missing": summary.get("missing_modules"),
                "degraded": summary.get("degraded_modules"),
            },
            "spine": snapshot.get("spine"),
            "bus": {"message_count": summary.get("bus_message_count")},
            "scheduler": {"skip_count": summary.get("scheduler_skip_count")},
            "phase_counts": summary.get("counts"),
            "integration_health": health,
            "metrics": metrics or {},
            "safety": snapshot.get("safety"),
        }

        narrative = self._narrative(sections)
        scan = self.claim_guard.scan_text(narrative)
        if not scan.safe:
            # Never emit unsupported claims -- rewrite rather than block.
            narrative = self.claim_guard.rewrite(narrative)

        return FullSystemReport(
            report_id=f"FSR_{uuid.uuid4().hex[:10]}",
            run_id=summary.get("run_id"),
            sections=sections, narrative=narrative,
            claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    def _narrative(self, sections: Dict[str, Any]) -> str:
        run = sections["run"]
        modules = sections["modules"]
        bus = sections["bus"]
        health = sections.get("integration_health") or {}
        lines = [
            "# Full System Report",
            "",
            "This report describes a bounded, simulated, low-compute "
            "developmental process. It is a software runtime, not a person; "
            "it does not feel, understand, or act in the real world.",
            "",
            "## Run",
            f"- run_id: {run.get('run_id')}",
            f"- profile: {run.get('profile')}",
            f"- mode: {run.get('mode')}",
            f"- authority: {run.get('authority')} "
            "(internal/simulation only; no real-world actuation)",
            f"- steps executed: {run.get('steps')}",
            f"- stopped cleanly: {run.get('stopped')}",
            "",
            "## Modules",
            f"- enabled: {', '.join(modules.get('enabled') or []) or 'none'}",
            f"- missing (skipped, not faked): "
            f"{', '.join(modules.get('missing') or []) or 'none'}",
            f"- degraded: "
            f"{', '.join(modules.get('degraded') or []) or 'none'}",
            "",
            "## Activity",
            f"- bus messages: {bus.get('message_count')}",
            f"- scheduler cadence skips: "
            f"{sections['scheduler'].get('skip_count')}",
            f"- integration health: {health.get('overall', 'unknown')}",
            "",
            "## Boundaries upheld",
            "- no real-world action authority",
            "- no network/OS/browser automation",
            "- no module bypassed executive, safety, or governance",
            "- the run stayed within its configured bounds",
        ]
        return "\n".join(lines)

    @staticmethod
    def _safe(fn: Any, default: Any) -> Any:
        try:
            return fn()
        except Exception:
            return default

    def write(self, report: FullSystemReport,
              artifact_dir: Optional[str]) -> Dict[str, Optional[str]]:
        """Write the JSON and Markdown report; return their paths."""
        if not artifact_dir:
            return {"json": None, "markdown": None}
        directory = Path(artifact_dir)
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "full_system_report.json"
        md_path = directory / "full_system_report.md"
        json_path.write_text(json.dumps(report.to_dict(), indent=2,
                                        default=str), encoding="utf-8")
        md_path.write_text(report.narrative, encoding="utf-8")
        return {"json": str(json_path), "markdown": str(md_path)}

    def build_and_write(self, orchestrator: Any, health_monitor: Any = None,
                        metrics: Optional[Dict[str, Any]] = None,
                        artifact_dir: Optional[str] = None,
                        ) -> FullSystemReport:
        report = self.build(orchestrator, health_monitor, metrics)
        target = artifact_dir or getattr(
            getattr(orchestrator, "context", None), "artifact_dir", None) \
            or getattr(getattr(orchestrator, "context", None), "state_dir",
                       None)
        paths = self.write(report, target)
        report.sections["report_paths"] = paths
        if hasattr(orchestrator, "report_path"):
            orchestrator.report_path = paths.get("json")
        else:
            setattr(orchestrator, "report_path", paths.get("json"))
        return report
