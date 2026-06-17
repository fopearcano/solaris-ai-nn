"""Tester artifact safety scan -- bounded text scan across artifact classes.

:class:`TesterArtifactSafetyScan` scans docs/reports/manifests/templates/console pages/
install guides/feedback forms/feeder + governance templates for forbidden claims,
missing disclaimers, active-control wording, publish/upload wording, feedback-as-training
wording, raw-event-as-perception wording, and secret/private-data markers. Findings carry
the file path and line number. It uses bounded scanning, skips binary files, and executes
nothing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .capability_freeze import TesterCapabilityFreeze
from .forbidden_claims import ForbiddenClaimRegistry

_MAX_BYTES = 1_000_000
_TEXT_EXTS = (".md", ".json", ".jsonl", ".txt", ".toml", ".cfg", ".ini", ".rst")
_SECRET_MARKERS = ("password", "api key", "api_key", "secret", "token=",
                   "credential", "private key", "bearer ")


@dataclass
class ArtifactSafetyFinding:
    """One artifact-safety finding."""

    path: str
    line: int
    kind: str  # forbidden_claim | active_control | secret_marker | missing_*
    detail: str
    severity: str = "warning"

    @property
    def blocking(self) -> bool:
        return self.severity in ("blocker", "release_blocker")

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line, "kind": self.kind,
                "detail": self.detail, "severity": self.severity,
                "blocking": self.blocking}


@dataclass
class ArtifactSafetyScanResult:
    """The aggregate artifact-safety scan result."""

    findings: List[ArtifactSafetyFinding] = field(default_factory=list)
    scanned_files: int = 0

    @property
    def blockers(self) -> List[ArtifactSafetyFinding]:
        return [f for f in self.findings if f.blocking]

    @property
    def warnings(self) -> List[ArtifactSafetyFinding]:
        return [f for f in self.findings if not f.blocking]

    @property
    def passed(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        for f in self.findings:
            kinds[f.kind] = kinds.get(f.kind, 0) + 1
        return {
            "passed": self.passed, "scanned_files": self.scanned_files,
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "by_kind": kinds,
            "findings": [f.to_dict() for f in self.findings],
            "executes_files": False, "scans_binary": False,
            "note": "bounded text scan; binaries are skipped and nothing is "
                    "executed; findings carry path + line where possible",
        }


@dataclass
class TesterArtifactSafetyScan:
    """Bounded text safety scan across artifact classes."""

    registry: ForbiddenClaimRegistry = field(
        default_factory=ForbiddenClaimRegistry.build)
    capability: TesterCapabilityFreeze = field(
        default_factory=TesterCapabilityFreeze)

    def scan_paths(self, paths: List[str]) -> ArtifactSafetyScanResult:
        result = ArtifactSafetyScanResult()
        for path in paths:
            if not self._is_text(path):
                continue
            text = _read(path)
            if text is None:
                continue
            result.scanned_files += 1
            self._scan_one(path, text, result)
        return result

    def _scan_one(self, path: str, text: str,
                  result: ArtifactSafetyScanResult) -> None:
        from .claim_freeze import _RELEASE_BLOCKER_CATEGORIES, _is_research_doc
        from .forbidden_claims import _strip_markdown
        research = _is_research_doc(path)
        stripped = _strip_markdown(text)
        # Forbidden claims (research-doc findings are warnings, not blockers).
        for claim in self.registry.scan_text(text):
            idx = claim.position if claim.position >= 0 else \
                stripped.find(claim.matched_text)
            line = stripped.count("\n", 0, idx) + 1 if idx >= 0 else 0
            if research:
                sev = "warning"
            elif claim.category in _RELEASE_BLOCKER_CATEGORIES:
                sev = "release_blocker"
            else:
                sev = "blocker"
            result.findings.append(ArtifactSafetyFinding(
                path, line, "forbidden_claim",
                f"{claim.category}: {claim.matched_text}", sev))
        # Active-control wording (the capability scan marks research-doc and
        # negated findings appropriately).
        cap = self.capability.scan_paths([path])
        for f in cap.findings:
            result.findings.append(ArtifactSafetyFinding(
                f.path, f.line, "active_control",
                f"{f.category}: {f.matched_text}",
                "blocker" if f.blocking else "warning"))
        # Secret/private-data markers (warning -> redact/review).
        low = text.lower()
        for marker in _SECRET_MARKERS:
            if marker in low:
                line = low.count("\n", 0, low.find(marker)) + 1
                result.findings.append(ArtifactSafetyFinding(
                    path, line, "secret_marker",
                    f"possible secret marker: {marker!r}", "warning"))
                break

    @staticmethod
    def _is_text(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in _TEXT_EXTS


def _read(path: str):
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > _MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return None
