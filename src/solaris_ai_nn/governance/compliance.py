"""ClaimGuard -- keeps generated text honest about what the system is.

Reports may describe measured behaviour ("produced a Desire signal",
"maintained continuity metrics", "consciousness-inspired signal flow") but may
not assert inner states the project cannot support ("the system is conscious",
"it understands", "it wants"). ClaimGuard scans generated text for such
unsupported claims and suggests grounded replacements.

It is a regex scanner over a fixed claim list -- deterministic, no NLP.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Pattern, Tuple

# (claim_type, compiled pattern, safer replacement guidance)
_SUBJECT = r"(?:the\s+)?(?:system|substrate|network|model|sidecar|brain|it)"

UNSUPPORTED_CLAIM_PATTERNS: List[Tuple[str, Pattern[str], str]] = [
    ("consciousness_claim",
     re.compile(r"\b(?:is|are|was|became|becomes)\s+conscious\b", re.I),
     "describe the design as 'consciousness-inspired' signal flow"),
    ("free_will_claim",
     re.compile(r"\bha(?:s|ve)\s+free\s+will\b", re.I),
     "describe the measured choice: 'suggested an action' with a confidence"),
    ("understanding_claim",
     re.compile(rf"\b{_SUBJECT}\s+(?:truly\s+|really\s+)?understands?\b", re.I),
     "state the measured mapping, e.g. 'mapped the stimulus to an action "
     "tendency'"),
    ("desire_claim",
     re.compile(rf"\b{_SUBJECT}\s+(?:wants|wanted|wishes|craves)\b", re.I),
     "say 'produced a Desire signal' (a named signal type, not a mental "
     "state)"),
    ("alive_claim",
     re.compile(rf"\b{_SUBJECT}\s+(?:is|was)\s+(?:truly\s+)?alive\b", re.I),
     "say 'maintained continuity metrics' or 'continued updating during "
     "silence'"),
    ("sentience_claim",
     re.compile(r"\b(?:is|are|was|became)\s+sentient\b", re.I),
     "describe the design as 'consciousness-inspired'; no sentience claim is "
     "supported"),
    ("feeling_claim",
     re.compile(rf"\b{_SUBJECT}\s+(?:feels|felt|suffers|enjoys)\b", re.I),
     "state the measured valence: 'recorded a Reaction with valence ...'"),
    ("self_awareness_claim",
     re.compile(r"\b(?:is|are|became)\s+self[- ]aware\b", re.I),
     "say 'updated its Inner MAP self-model' (a data structure, not "
     "awareness)"),
]

# Phrasings that are always acceptable (documented for tests and authors).
SAFE_PHRASES = [
    "consciousness-inspired",
    "produced a Desire signal",
    "suggested an action",
    "adapted a runtime parameter",
    "continued updating during silence",
    "maintained continuity metrics",
]


@dataclass
class ClaimGuardFinding:
    """One flagged claim: where it is, what it says, what to say instead."""

    claim_type: str
    phrase: str
    position: int
    suggestion: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ClaimGuardReport:
    """Result of scanning one text."""

    safe: bool
    findings: List[ClaimGuardFinding] = field(default_factory=list)
    scanned_chars: int = 0
    timestamp: float = field(default_factory=time.time)

    def suggestions(self) -> List[str]:
        return [f.suggestion for f in self.findings]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe": self.safe,
            "scanned_chars": self.scanned_chars,
            "timestamp": self.timestamp,
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ClaimGuard:
    """Scans generated text for unsupported claims about inner states."""

    def scan_text(self, text: str) -> ClaimGuardReport:
        findings: List[ClaimGuardFinding] = []
        for claim_type, pattern, suggestion in UNSUPPORTED_CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(ClaimGuardFinding(
                    claim_type=claim_type, phrase=match.group(0),
                    position=match.start(), suggestion=suggestion))
        findings.sort(key=lambda f: f.position)
        return ClaimGuardReport(safe=not findings, findings=findings,
                                scanned_chars=len(text))

    def is_safe(self, text: str) -> bool:
        return self.scan_text(text).safe

    def suggest_replacements(self, text: str) -> List[str]:
        """Human-readable 'instead of X, say Y' lines for each flagged claim."""
        return [f"instead of {f.phrase!r}: {f.suggestion}"
                for f in self.scan_text(text).findings]

    def rewrite(self, text: str) -> str:
        """Replace each flagged claim with an explicitly hedged marker.

        The replacement keeps the report readable while making it impossible
        to mistake the flagged phrase for a supported claim.
        """
        result = text
        for claim_type, pattern, _ in UNSUPPORTED_CLAIM_PATTERNS:
            result = pattern.sub(
                f"[unsupported {claim_type} removed by ClaimGuard]", result)
        return result

    def warning_section(self, report: ClaimGuardReport) -> str:
        """A Markdown section describing the flagged claims."""
        lines = ["## Claim Guard Warnings", "",
                 f"{len(report.findings)} unsupported claim(s) were flagged "
                 "in this report:", ""]
        for f in report.findings:
            lines.append(f"- {f.phrase!r} ({f.claim_type}): {f.suggestion}")
        lines.append("")
        return "\n".join(lines)
