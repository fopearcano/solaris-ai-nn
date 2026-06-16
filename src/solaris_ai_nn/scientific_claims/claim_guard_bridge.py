"""ClaimGuard bridge -- scan generated text; ClaimGuard failure blocks readiness.

:class:`ClaimGuardBridge` scans generated claim reports, abstracts, publication
dossiers, README-safe summaries, and theory ledger statements through ClaimGuard.
A ClaimGuard failure blocks publication readiness; a missing ClaimGuard produces a
warning or a blocker depending on config; and ClaimGuard is never bypassed.
Explicit disclaimers are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClaimGuardBridgeResult:
    """The result of scanning one text through ClaimGuard."""

    label: str
    safe: bool
    finding_count: int = 0
    findings: List[Dict[str, Any]] = field(default_factory=list)
    claim_guard_available: bool = True
    blocks_readiness: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "safe": self.safe,
                "finding_count": self.finding_count,
                "findings": list(self.findings),
                "claim_guard_available": self.claim_guard_available,
                "blocks_readiness": self.blocks_readiness}


@dataclass
class ClaimGuardBridge:
    """Bridges the scientific claim layer to the governance ClaimGuard."""

    require_claimguard: bool = True
    block_count: int = field(default=0, init=False)
    results: List[ClaimGuardBridgeResult] = field(default_factory=list,
                                                  init=False)

    def _guard(self):
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard()
        except Exception:
            return None

    def scan(self, label: str, text: str) -> ClaimGuardBridgeResult:
        guard = self._guard()
        if guard is None:
            # Missing ClaimGuard: warn unless required (then block).
            result = ClaimGuardBridgeResult(
                label=label, safe=not self.require_claimguard,
                claim_guard_available=False,
                blocks_readiness=self.require_claimguard)
            if result.blocks_readiness:
                self.block_count += 1
            self.results.append(result)
            return result
        report = guard.scan_text(text or "")
        result = ClaimGuardBridgeResult(
            label=label, safe=report.safe,
            finding_count=len(report.findings),
            findings=[f.to_dict() for f in report.findings],
            claim_guard_available=True,
            blocks_readiness=not report.safe)
        if result.blocks_readiness:
            self.block_count += 1
        self.results.append(result)
        return result

    def scan_many(self, items: Dict[str, str]) -> List[ClaimGuardBridgeResult]:
        return [self.scan(label, text) for label, text in items.items()]

    @property
    def claimguard_block_count(self) -> int:
        return self.block_count

    @property
    def any_blocked(self) -> bool:
        return self.block_count > 0

    def rewrite(self, text: str) -> str:
        guard = self._guard()
        if guard is None:
            return text
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
        return text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claimguard_block_count": self.block_count,
            "scanned_count": len(self.results),
            "any_blocked": self.any_blocked,
            "results": [r.to_dict() for r in self.results],
            "note": "ClaimGuard failure blocks publication readiness; ClaimGuard "
                    "is never bypassed and allowed disclaimers are preserved",
        }
