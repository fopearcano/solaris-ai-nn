"""LLM claim filter -- ClaimGuard wrapped around the adapter boundary.

Pre-scans allowed facts before they enter a prompt, post-scans every
output, suggests safe rewrites for forbidden phrasing, and enforces a
final refusal when rewriting cannot make the text safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LLMClaimFilter:
    """Pre/post ClaimGuard scanning with rewrite-then-refuse semantics."""

    pre_scan_failures: int = field(default=0, init=False)
    post_scan_failures: int = field(default=0, init=False)
    rewrites_applied: int = field(default=0, init=False)
    refusals: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        from ..governance.compliance import ClaimGuard

        self.guard = ClaimGuard()

    # -- scans --------------------------------------------------------------------

    def pre_scan_facts(self, facts: List[str]) -> List[str]:
        """Drop facts ClaimGuard flags before they ever reach a prompt."""
        safe: List[str] = []
        for fact in facts:
            if self.guard.is_safe(str(fact)):
                safe.append(str(fact))
            else:
                self.pre_scan_failures += 1
        return safe

    def post_scan(self, text: str) -> bool:
        ok = self.guard.is_safe(str(text))
        if not ok:
            self.post_scan_failures += 1
        return ok

    def suggest_rewrite(self, text: str) -> str:
        return self.guard.rewrite(str(text))

    # -- enforcement ----------------------------------------------------------------

    def enforce(self, text: str) -> "tuple[bool, str]":
        """(ok, safe_text). Rewrite once; if still unsafe, refuse."""
        if self.post_scan(text):
            return (True, str(text))
        rewritten = self.suggest_rewrite(text)
        if self.guard.is_safe(rewritten):
            self.rewrites_applied += 1
            return (True, rewritten)
        self.refusals += 1
        return (False, "")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pre_scan_failures": self.pre_scan_failures,
            "post_scan_failures": self.post_scan_failures,
            "rewrites_applied": self.rewrites_applied,
            "refusals": self.refusals,
        }
