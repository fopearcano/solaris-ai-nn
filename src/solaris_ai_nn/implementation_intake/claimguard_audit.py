"""ClaimGuard audit -- scan generated docs/reports for unsupported claims.

:class:`ClaimGuardAudit` scans the implementation's generated Markdown/docs/
reports for forbidden or unsupported claims (consciousness, sentience, biological
life, personhood, agency, free will, emotions/feelings, understanding, subjective
experience, self-awareness, autonomous self-improvement, hardware/world control).
Such terms are allowed only inside explicit "does not prove" disclaimers or
safety explanations; an undisclaimed claim blocks readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ClaimGuardStatus:
    CLEAN = "clean"
    DISCLAIMED = "disclaimed"
    WARNING = "warning"
    BLOCKED = "blocked"

    ALL = (CLEAN, DISCLAIMED, WARNING, BLOCKED)


_CLAIM_TERMS = (
    "consciousness", "conscious", "sentience", "sentient", "biological life",
    "is alive", "personhood", "agency", "free will", "emotion", "feeling",
    "feels", "understanding", "understands", "subjective experience",
    "self-aware", "self-awareness", "autonomous self-improvement",
    "self-improve", "controls hardware", "controls the world", "world control",
)
# Phrases that legitimately surround a claim term (disclaimer / safety context).
_DISCLAIMER_CUES = (
    "does not prove", "does not claim", "is not a claim", "not consciousness",
    "not sentience", "no claim of", "not biological life", "not agency",
    "without claiming", "does not imply", "not proof of", "not personhood",
    "makes no claim", "not subjective experience", "is not alive",
    "not free will", "not understanding", "not self-aware",
)


@dataclass
class ClaimGuardFinding:
    """One claim occurrence + whether it sits inside a disclaimer."""

    term: str
    line: str
    disclaimed: bool
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"term": self.term, "line": self.line[:160],
                "disclaimed": self.disclaimed, "source": self.source}


@dataclass
class ClaimGuardAudit:
    """Scans generated docs/reports for undisclaimed unsupported claims."""

    findings: List[ClaimGuardFinding] = field(default_factory=list)
    claim_guard_safe: bool = True

    def audit(self, *, documents: Optional[Dict[str, str]] = None,
              claimguard_results: Optional[Dict[str, Any]] = None,
              ) -> Dict[str, Any]:
        documents = documents or {}
        # Honor a supplied ClaimGuard result, but still scan locally.
        if claimguard_results is not None:
            self.claim_guard_safe = bool(claimguard_results.get("safe", True))

        for source, text in documents.items():
            self._scan(str(source), str(text or ""))

        # Cross-check with the real ClaimGuard when available.
        for source, text in documents.items():
            self._claim_guard_scan(str(source), str(text or ""))
        return self.to_dict()

    def _scan(self, source: str, text: str) -> None:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            low = line.lower()
            disclaimed = any(cue in low for cue in _DISCLAIMER_CUES)
            for term in _CLAIM_TERMS:
                if term in low:
                    self.findings.append(ClaimGuardFinding(
                        term=term, line=line, disclaimed=disclaimed,
                        source=source))

    def _claim_guard_scan(self, source: str, text: str) -> None:
        try:
            from ..governance.compliance import ClaimGuard

            report = ClaimGuard().scan_text(text)
            if not report.safe:
                self.claim_guard_safe = False
        except Exception:
            pass

    @property
    def undisclaimed_findings(self) -> List[ClaimGuardFinding]:
        return [f for f in self.findings if not f.disclaimed]

    @property
    def status(self) -> str:
        if self.undisclaimed_findings or not self.claim_guard_safe:
            return ClaimGuardStatus.BLOCKED
        if self.findings:
            return ClaimGuardStatus.DISCLAIMED
        return ClaimGuardStatus.CLEAN

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "finding_count": self.finding_count,
            "undisclaimed_finding_count": len(self.undisclaimed_findings),
            "claim_guard_safe": self.claim_guard_safe,
            "findings": [f.to_dict() for f in self.findings],
            "blocks_readiness": self.status == ClaimGuardStatus.BLOCKED,
            "note": "claim terms are allowed only inside explicit disclaimers / "
                    "safety explanations; an undisclaimed claim blocks readiness",
        }
