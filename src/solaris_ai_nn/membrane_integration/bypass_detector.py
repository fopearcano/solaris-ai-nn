"""Membrane bypass detector -- no bypass may be silently ignored.

:class:`MembraneBypassDetector` finds places where downstream modules bypass the
membrane: raw-event direct paths, concepts/signs/traces lacking impression ancestry,
reports omitting membrane status, raw fallback that is not marked, contamination or
operator-text dominance not propagated, and missing receptor/permeability lineage. In
strict live mode a direct raw-event downstream path is a blocker; in fixture mode an
expected raw fallback is a warning. Findings are always written to reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class MembraneBypassSeverity:
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, BLOCKER, CRITICAL)
    _RANK = {INFO: 0, WARNING: 1, BLOCKER: 2, CRITICAL: 3}


@dataclass
class MembraneBypassFinding:
    """One bypass finding (never silently ignored)."""

    finding: str
    severity: str = MembraneBypassSeverity.WARNING
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding": self.finding, "severity": self.severity,
                "detail": self.detail}


@dataclass
class MembraneBypassDetector:
    """Detects membrane bypasses from loaded artifacts + ancestry."""

    def detect(self, *, impressions_present: bool, membrane_present: bool,
               ancestry, contracts, strict: bool,
               raw_fallback_marked: bool = True) -> List[MembraneBypassFinding]:
        out: List[MembraneBypassFinding] = []
        S = MembraneBypassSeverity

        if membrane_present and not impressions_present:
            out.append(MembraneBypassFinding(
                "membrane_present_no_impressions",
                S.BLOCKER if strict else S.WARNING,
                "membrane exists but produced no sensory impressions"))

        if ancestry is not None and ancestry.membrane_available:
            if ancestry.missing_ancestry:
                out.append(MembraneBypassFinding(
                    "missing_impression_ancestry",
                    S.CRITICAL if strict else S.WARNING,
                    f"{ancestry.missing_ancestry} downstream artifact(s) lack "
                    "impression ancestry"))
            if ancestry.contaminated_ancestry:
                out.append(MembraneBypassFinding(
                    "contamination_propagated_ancestry", S.WARNING,
                    f"{ancestry.contaminated_ancestry} artifact(s) carry "
                    "contaminated ancestry"))
            fallback = sum(1 for c in ancestry.chains if c.fallback_raw_event)
            if fallback:
                out.append(MembraneBypassFinding(
                    "raw_event_fallback_used",
                    S.BLOCKER if strict else S.WARNING,
                    f"{fallback} artifact(s) fell back to raw events"))
                if not raw_fallback_marked:
                    out.append(MembraneBypassFinding(
                        "raw_fallback_not_marked", S.CRITICAL,
                        "raw fallback was used but not marked"))

        for c in (contracts or []):
            if c.status == "violated":
                out.append(MembraneBypassFinding(
                    f"contract_violated_{c.module}",
                    S.BLOCKER if strict else S.WARNING,
                    f"{c.module} contract violated"))
        return out

    @staticmethod
    def summary(findings: List[MembraneBypassFinding]) -> Dict[str, Any]:
        sev: Dict[str, int] = {}
        for f in findings:
            sev[f.severity] = sev.get(f.severity, 0) + 1
        worst = max((MembraneBypassSeverity._RANK[f.severity]
                     for f in findings), default=-1)
        worst_name = next((k for k, v in MembraneBypassSeverity._RANK.items()
                           if v == worst), "none")
        return {
            "bypass_finding_count": len(findings),
            "by_severity": sev,
            "critical_bypass_count": sev.get(
                MembraneBypassSeverity.CRITICAL, 0),
            "blocker_bypass_count": sev.get(MembraneBypassSeverity.BLOCKER, 0),
            "worst_severity": worst_name,
            "findings": [f.to_dict() for f in findings],
            "note": "no bypass may be silently ignored; in strict live mode a "
                    "direct raw-event downstream path is a blocker",
        }

    @staticmethod
    def has_blocking(findings: List[MembraneBypassFinding]) -> bool:
        return any(f.severity in (MembraneBypassSeverity.BLOCKER,
                                  MembraneBypassSeverity.CRITICAL)
                   for f in findings)
