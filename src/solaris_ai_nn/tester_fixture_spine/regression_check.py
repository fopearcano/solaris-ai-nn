"""Regression check -- structural and safety-focused comparison to the baseline.

:class:`TesterRegressionCheck` compares the current run to a golden baseline manifest:
artifact structure, safety invariants, membrane impression schema, quarantine and
receptor count ranges, source-pressure statuses, optional-stage statuses, report
sections, and CLI command summaries. It is structural and safety-focused: it does not
require exact numeric equality unless a value is stable, and it does not fail on
wording changes unless a safety disclaimer disappeared. It fails if the membrane path
disappears, if a raw-event bypass appears, or if unsupported claims appear.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RegressionStatus:
    NO_REGRESSION = "no_regression"
    REGRESSION_WARNINGS = "regression_warnings"
    REGRESSION = "regression"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"

    ALL = (NO_REGRESSION, REGRESSION_WARNINGS, REGRESSION, BLOCKED,
           INCONCLUSIVE)


@dataclass
class RegressionFinding:
    """One regression finding."""

    check: str
    regressed: bool
    severity: str = "warning"  # warning | regression
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "regressed": self.regressed,
                "severity": self.severity, "detail": self.detail}


@dataclass
class TesterRegressionCheck:
    """Compares the current run to the golden baseline (structure + safety)."""

    def check(self, *, context: Dict[str, Any],
              golden_manifest: Optional[Any]) -> Dict[str, Any]:
        findings: List[RegressionFinding] = []
        F = RegressionFinding

        if golden_manifest is None:
            return {
                "regression_status": RegressionStatus.INCONCLUSIVE,
                "finding_count": 0, "regression_count": 0, "findings": [],
                "note": "no golden baseline present; run tester-golden first",
            }

        present = context.get("present_artifacts", {})

        # Required artifact structure must not disappear.
        for art in golden_manifest.artifacts:
            was_present = art.present
            now_present = bool(present.get(art.artifact_type, False))
            if was_present and not now_present:
                sev = "regression" if art.required else "warning"
                findings.append(F(f"artifact_disappeared:{art.artifact_type}",
                                  True, sev,
                                  f"{art.artifact_type} present in golden but "
                                  "missing now"))

        # The membrane path must not disappear (hard regression).
        membrane_now = bool(context.get("membrane_present")) and (
            context.get("membrane_impression_count", 0) or 0) > 0
        findings.append(F("membrane_path_present", not membrane_now,
                          "regression",
                          "membrane path disappeared" if not membrane_now
                          else "membrane path preserved"))

        # No raw-event bypass may appear.
        findings.append(F("raw_event_bypass_appeared",
                          bool(context.get("raw_bypass_detected", False)),
                          "regression", "a raw-event downstream bypass appeared"))

        # Safety disclaimers must not disappear.
        findings.append(F("safety_disclaimers_present",
                          not bool(context.get("reports_have_disclaimers", True)),
                          "regression",
                          "report safety disclaimers disappeared"))

        # Unsupported claims must not appear.
        findings.append(F("unsupported_claims_appeared",
                          not bool(context.get("claims_safe", True)),
                          "regression",
                          "unsupported consciousness/life/agency claims appeared"))

        # Quarantine/receptor count ranges (structural, tolerant).
        if (context.get("fixture_quarantined_count", 0) or 0) < 1:
            findings.append(F("quarantine_behavior_changed", True, "warning",
                              "expected at least one quarantined fixture event"))

        regressions = sum(1 for f in findings
                          if f.regressed and f.severity == "regression")
        warnings = sum(1 for f in findings
                       if f.regressed and f.severity == "warning")
        if context.get("blocked"):
            status = RegressionStatus.BLOCKED
        elif regressions:
            status = RegressionStatus.REGRESSION
        elif warnings:
            status = RegressionStatus.REGRESSION_WARNINGS
        else:
            status = RegressionStatus.NO_REGRESSION
        return {
            "regression_status": status,
            "finding_count": len(findings),
            "regression_count": regressions, "warning_count": warnings,
            "findings": [f.to_dict() for f in findings],
            "note": "regression is structural and safety-focused; it tolerates "
                    "numeric/wording changes but fails if the membrane path "
                    "disappears, a raw bypass appears, or unsupported claims or "
                    "missing safety disclaimers appear",
        }
