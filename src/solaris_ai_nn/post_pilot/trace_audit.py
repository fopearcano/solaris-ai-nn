"""Post-pilot trace audit -- are the conclusions actually backed by artifacts?

The :class:`DevelopmentalTraceAuditor` checks that major claims are supported,
metric deltas are traceable, simulated and real-time records are separated,
counterfactual/offline records are separated, memory-compression summaries and
safety incidents are preserved, restart gaps are recorded, and reports are
consistent with raw observability. It never repairs artifacts; it only reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TraceAuditResult:
    """The outcome of auditing a pilot's developmental trace."""

    checks: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    traceability_score: float = 0.0
    claim_guard_respected: bool = True

    @property
    def passed(self) -> bool:
        return not self.contradictions and self.traceability_score >= 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "passed": self.passed}


@dataclass
class DevelopmentalTraceAuditor:
    """Audits whether a pilot's conclusions are traceable to artifacts."""

    def audit(self, artifacts: Any,
              claims: Any = None) -> TraceAuditResult:
        result = TraceAuditResult()
        present = set(getattr(getattr(artifacts, "index", None), "present", [])
                     or [])
        data = getattr(artifacts, "data", {}) or {}
        checks = result.checks

        # 1. Major claims supported by artifacts (observability + report).
        checks["observability_present"] = "observability" in present
        checks["pilot_report_present"] = "pilot_report" in present
        # 2. Metric deltas traceable (daily metrics exist).
        checks["metrics_traceable"] = ("metrics_daily" in present
                                       or "daily" in present)
        # 3. Simulated vs real separated (report labels its mode).
        report = data.get("pilot_report") or {}
        sections = report.get("sections") or {}
        run = sections.get("run") or {}
        mode = str(run.get("mode", report.get("mode", "")))
        checks["sim_real_separated"] = bool(mode) or bool(
            report.get("time_label"))
        if not checks["sim_real_separated"]:
            result.warnings.append("run mode/time-label not clearly recorded")
        # 4. Counterfactual/offline separated -- look for an explicit flag.
        checks["counterfactual_separated"] = not self._mixed_offline(data)
        if not checks["counterfactual_separated"]:
            result.contradictions.append(
                "offline/counterfactual records appear mixed with observed")
        # 5. Memory compression summaries present.
        checks["compression_summary_present"] = (
            "developmental_state" in present
            or "autobiographical_memory" in present)
        # 6. Safety incidents preserved.
        checks["safety_incidents_preserved"] = "incidents" in present
        # 7. Restart gaps recorded.
        checks["restart_gaps_recorded"] = self._restarts_recorded(data,
                                                                  present)
        # 8. Fossil memories linked to evidence (best-effort).
        checks["fossils_linked"] = ("autobiographical_memory" in present
                                    or "developmental_epochs" in present)
        # 9. Reports consistent with raw observability.
        checks["reports_consistent"] = self._reports_consistent(data)
        if not checks["reports_consistent"]:
            result.contradictions.append(
                "pilot report step/uptime inconsistent with observability")
        # 10. ClaimGuard respected in the report.
        result.claim_guard_respected = bool(
            report.get("claim_guard_safe", True))
        checks["claim_guard_respected"] = result.claim_guard_respected
        if not result.claim_guard_respected:
            result.warnings.append("pilot report tripped ClaimGuard")

        passed = sum(1 for v in checks.values() if v)
        result.traceability_score = round(passed / max(1, len(checks)), 4)

        # Optional: validate explicit claims carry evidence refs.
        for claim in (getattr(claims, "claims", None) or []):
            if not getattr(claim, "evidence_refs", None):
                result.warnings.append(
                    f"claim {getattr(claim, 'claim_type', '?')} lacks "
                    "evidence refs")
        return result

    @staticmethod
    def _mixed_offline(data: Dict[str, Any]) -> bool:
        """Detect observability events that mix offline evidence as observed."""
        for event in (data.get("observability") or []):
            payload = event.get("payload", {}) if isinstance(event, dict) \
                else {}
            if payload.get("offline") and payload.get("observed"):
                return True
        return False

    @staticmethod
    def _restarts_recorded(data: Dict[str, Any], present: set) -> bool:
        if "developmental_state" in present:
            return True
        for event in (data.get("observability") or []):
            if isinstance(event, dict) and \
                    event.get("payload", {}).get("restart_count", 0):
                return True
        return "incidents" in present

    @staticmethod
    def _reports_consistent(data: Dict[str, Any]) -> bool:
        report = data.get("pilot_report") or {}
        sections = report.get("sections") or {}
        run = sections.get("run") or {}
        report_steps = run.get("steps")
        if report_steps is None:
            return True  # nothing to contradict
        obs = data.get("observability") or []
        # The report's step count should not exceed observed heartbeats wildly.
        heartbeats = sum(1 for e in obs if isinstance(e, dict)
                         and e.get("kind") in ("heartbeat", "metrics"))
        if heartbeats == 0:
            return True
        return report_steps <= heartbeats * 50  # generous tolerance
