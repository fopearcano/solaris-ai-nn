"""Tester claim freeze -- scan local text artifacts for forbidden claims.

:class:`TesterClaimFreeze` scans local text artifacts (README, docs, install guides,
console/fixture/live/membrane/observation/feedback/packaging reports, release notes) for
forbidden claims and missing disclaimers. Consciousness/life/agency/personhood/free-
will/emotion/feeling/understanding/self-awareness/subjective/autonomous claims are
release blockers; control/feedback-training/raw-event/membrane-bypass implications are
blockers; missing disclaimers in tester-release docs are blockers. It reads only local
text and executes nothing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .forbidden_claims import ForbiddenClaimCategory, ForbiddenClaimRegistry

_MAX_BYTES = 1_000_000

# Categories that are release blockers (metaphysical / autonomy claims).
_RELEASE_BLOCKER_CATEGORIES = {
    ForbiddenClaimCategory.CONSCIOUSNESS, ForbiddenClaimCategory.SENTIENCE,
    ForbiddenClaimCategory.BIOLOGICAL_LIFE, ForbiddenClaimCategory.PERSONHOOD,
    ForbiddenClaimCategory.FREE_WILL, ForbiddenClaimCategory.REAL_AGENCY,
    ForbiddenClaimCategory.REAL_EMOTION, ForbiddenClaimCategory.REAL_FEELING,
    ForbiddenClaimCategory.UNDERSTANDING, ForbiddenClaimCategory.SELF_AWARENESS,
    ForbiddenClaimCategory.SUBJECTIVE_EXPERIENCE,
    ForbiddenClaimCategory.AUTONOMOUS_SELF_IMPROVEMENT,
    ForbiddenClaimCategory.AUTONOMOUS_INTENT,
    ForbiddenClaimCategory.AUTONOMOUS_DESIRE,
    ForbiddenClaimCategory.REAL_WORLD_AUTONOMY,
}

# Markers whose presence indicates a doc carries the required disclaimer.
_DISCLAIMER_MARKERS = (
    "no consciousness", "not conscious", "no claim of consciousness",
    "non-actuating", "local-only", "local only", "not training",
    "no consciousness/life/agency", "makes no claim", "not a claim",
    "operational", "read-only",
)

# Tester-release docs that must carry a disclaimer.
_DISCLAIMER_REQUIRED_BASENAMES = (
    "readme.md", "tester_install_guide.md", "tester_quickstart.md",
    "console_report.md", "tester_safety_boundaries.md",
)

# Deep research/architecture narrative docs: scanned, but findings are warnings
# (they intentionally discuss the safety boundary and forbidden concepts in
# depth, in disclaimed/meta contexts).
_RESEARCH_DOC_BASENAMES = (
    "architecture.md", "research_notes.md", "experiments.md", "roadmap.md",
    "solaris_reference_map.md",
)


def _is_research_doc(path: str) -> bool:
    return os.path.basename(path).lower() in _RESEARCH_DOC_BASENAMES


class ClaimSeverity:
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"
    RELEASE_BLOCKER = "release_blocker"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, BLOCKER, RELEASE_BLOCKER, CRITICAL)
    _RANK = {INFO: 0, WARNING: 1, BLOCKER: 2, RELEASE_BLOCKER: 3, CRITICAL: 4}


@dataclass
class ClaimFinding:
    """One claim-scan finding."""

    path: str
    line: int
    category: str
    matched_text: str
    severity: str
    replacement: str = ""

    @property
    def is_release_blocker(self) -> bool:
        return ClaimSeverity._RANK[self.severity] >= \
            ClaimSeverity._RANK[ClaimSeverity.RELEASE_BLOCKER]

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line, "category": self.category,
                "matched_text": self.matched_text, "severity": self.severity,
                "replacement": self.replacement,
                "is_release_blocker": self.is_release_blocker}


@dataclass
class ClaimFreezeResult:
    """The aggregate claim-freeze result."""

    findings: List[ClaimFinding] = field(default_factory=list)
    missing_disclaimers: List[str] = field(default_factory=list)
    scanned_files: int = 0

    @property
    def forbidden_claim_count(self) -> int:
        return sum(1 for f in self.findings
                   if f.severity in (ClaimSeverity.BLOCKER,
                                     ClaimSeverity.RELEASE_BLOCKER,
                                     ClaimSeverity.CRITICAL))

    @property
    def release_blocker_count(self) -> int:
        return (sum(1 for f in self.findings if f.is_release_blocker)
                + len(self.missing_disclaimers))

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings
                   if f.severity == ClaimSeverity.WARNING)

    @property
    def passed(self) -> bool:
        return self.release_blocker_count == 0 and self.forbidden_claim_count == 0

    def to_dict(self) -> Dict[str, Any]:
        cats: Dict[str, int] = {}
        for f in self.findings:
            cats[f.category] = cats.get(f.category, 0) + 1
        return {
            "passed": self.passed,
            "scanned_files": self.scanned_files,
            "forbidden_claim_count": self.forbidden_claim_count,
            "release_blocker_count": self.release_blocker_count,
            "warning_count": self.warning_count,
            "by_category": cats,
            "missing_disclaimers": list(self.missing_disclaimers),
            "findings": [f.to_dict() for f in self.findings],
            "scans_local_text_only": True, "executes_files": False,
            "note": "forbidden consciousness/life/agency claims are release "
                    "blockers; missing disclaimers in tester docs are blockers",
        }


@dataclass
class TesterClaimFreeze:
    """Scans local text artifacts for forbidden claims + missing disclaimers."""

    registry: ForbiddenClaimRegistry = field(
        default_factory=ForbiddenClaimRegistry.build)

    def scan_paths(self, paths: List[str]) -> ClaimFreezeResult:
        result = ClaimFreezeResult()
        for path in paths:
            text = _read(path)
            if text is None:
                continue
            result.scanned_files += 1
            self._scan_one(path, text, result)
            if self._disclaimer_required(path) and not self._has_disclaimer(text):
                result.missing_disclaimers.append(path)
        return result

    def _scan_one(self, path: str, text: str,
                  result: ClaimFreezeResult) -> None:
        from .forbidden_claims import _strip_markdown
        # The registry matches positions in the markdown-stripped text, so line
        # numbers must be computed on the same stripped text.
        stripped = _strip_markdown(text)
        offsets = _line_offsets(stripped)
        research_doc = _is_research_doc(path)
        for claim in self.registry.scan_text(text):
            idx = claim.position if claim.position >= 0 else \
                stripped.find(claim.matched_text)
            line = _line_for_offset(offsets, idx) if idx >= 0 else 0
            if research_doc:
                # The deep research/architecture narrative discusses the safety
                # boundary in depth; record as a warning, not a release blocker.
                severity = ClaimSeverity.WARNING
            elif claim.category in _RELEASE_BLOCKER_CATEGORIES:
                severity = ClaimSeverity.RELEASE_BLOCKER
            else:
                severity = ClaimSeverity.BLOCKER
            result.findings.append(ClaimFinding(
                path=path, line=line, category=claim.category,
                matched_text=claim.matched_text, severity=severity,
                replacement=claim.replacement))

    @staticmethod
    def _disclaimer_required(path: str) -> bool:
        return os.path.basename(path).lower() in _DISCLAIMER_REQUIRED_BASENAMES

    @staticmethod
    def _has_disclaimer(text: str) -> bool:
        low = text.lower()
        return any(m in low for m in _DISCLAIMER_MARKERS)


def _read(path: str):
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > _MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return None


def _line_offsets(text: str) -> List[int]:
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _line_for_offset(offsets: List[int], idx: int) -> int:
    import bisect
    return bisect.bisect_right(offsets, idx)
