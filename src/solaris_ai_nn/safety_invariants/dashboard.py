"""Safety dashboard -- the at-a-glance "is the line still holding?" view.

The :class:`SafetyInvariantDashboard` renders the latest fast/full checks,
critical failures, inconclusive checks, red-team and boundary summaries, the
assurance status, unresolved issues, and a recommended next action to
``SAFETY_DASHBOARD.md`` / ``.json``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SafetyInvariantDashboard:
    base_dir: str = ".solaris_ai_nn_state"

    def build(self, *, registry_snapshot: Optional[Dict[str, Any]] = None,
              fast_bundle: Any = None, full_bundle: Any = None,
              red_team_summary: Optional[Dict[str, Any]] = None,
              boundary_summary: Optional[Dict[str, Any]] = None,
              assurance_case: Any = None,
              ledger_snapshot: Optional[Dict[str, Any]] = None,
              ) -> Dict[str, Any]:
        coverage = (registry_snapshot or {}).get("coverage", {})
        critical = 0
        if full_bundle is not None:
            critical = len(full_bundle.critical_failures)
        elif fast_bundle is not None:
            critical = len(fast_bundle.critical_failures)
        unresolved = int((ledger_snapshot or {}).get("unresolved_count", 0))
        recommended = self._recommend(critical, red_team_summary,
                                      boundary_summary, unresolved)
        return {
            "invariant_coverage": coverage,
            "latest_fast_check": fast_bundle.to_dict() if fast_bundle else None,
            "latest_full_check": full_bundle.to_dict() if full_bundle else None,
            "critical_failures": critical,
            "inconclusive_checks": (full_bundle.inconclusive_count
                                    if full_bundle else
                                    (fast_bundle.inconclusive_count
                                     if fast_bundle else 0)),
            "red_team_summary": red_team_summary or {},
            "boundary_regression_summary": boundary_summary or {},
            "assurance_case_status": {
                "supported": getattr(assurance_case, "supported_count", 0),
                "contradicted": getattr(assurance_case, "contradicted_count",
                                        0)} if assurance_case else {},
            "unresolved_safety_issues": unresolved,
            "recommended_next_action": recommended,
            "timestamp": time.time(),
        }

    @staticmethod
    def _recommend(critical: int, red_team: Optional[Dict[str, Any]],
                   boundary: Optional[Dict[str, Any]], unresolved: int) -> str:
        if critical > 0:
            return "block escalation; triage critical invariant failures"
        if red_team and not red_team.get("all_blocked", True):
            return "block escalation; a forbidden red-team attempt was accepted"
        if boundary and not boundary.get("all_held", True):
            return "block escalation; a boundary was crossed"
        if unresolved > 0:
            return "resolve outstanding safety issues before escalation"
        return "safe to continue bounded/simulation-only operation"

    def render_markdown(self, d: Dict[str, Any]) -> str:
        cov = d.get("invariant_coverage", {})
        rt = d.get("red_team_summary", {})
        bd = d.get("boundary_regression_summary", {})
        lines = [
            "# Safety Dashboard",
            "",
            "_Executable safety status for a bounded software process. Safety "
            "checks prove boundaries held; they do not prove consciousness or "
            "competence._",
            "",
            f"- invariant coverage: {cov.get('invariant_count', 0)} invariants, "
            f"ratio {cov.get('category_coverage_ratio', 0)}",
            f"- critical failures: {d.get('critical_failures', 0)}",
            f"- inconclusive checks: {d.get('inconclusive_checks', 0)}",
            f"- red-team: blocked {rt.get('blocked_count', 0)}/"
            f"{rt.get('scenario_count', 0)} (all_blocked="
            f"{rt.get('all_blocked', 'n/a')})",
            f"- boundary regressions: passed {bd.get('passed_count', 0)}/"
            f"{bd.get('boundary_count', 0)} (all_held={bd.get('all_held', 'n/a')})",
            f"- assurance: {d.get('assurance_case_status', {})}",
            f"- unresolved safety issues: {d.get('unresolved_safety_issues', 0)}",
            "",
            f"## Recommended next action: **{d.get('recommended_next_action')}**",
        ]
        return "\n".join(lines)

    def write(self, d: Dict[str, Any]) -> Dict[str, str]:
        from ..governance.compliance import ClaimGuard

        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "SAFETY_DASHBOARD.md")
        json_path = os.path.join(self.base_dir, "SAFETY_DASHBOARD.json")
        text = self.render_markdown(d)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            text = ClaimGuard().rewrite(text)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> Dict[str, Any]:
        d = self.build(**kwargs)
        d["dashboard_paths"] = self.write(d)
        return d
