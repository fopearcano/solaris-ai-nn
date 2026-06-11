"""HomeostasisSafetyValidator -- needs are data; the walls stay up.

Hard rules: needs/drives have no execution path; nothing here can bypass
governance, block the emergency stop, or mint real-world actions out of
desire candidates; sidecars stay observe-only without approval;
``safe_shutdown_recommended`` is a recommendation that only the ops
supervisor/watchdog may act on; and reports stay free of anthropomorphic
claims (ClaimGuard re-checks at save time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..embodiment.safety import REAL_WORLD_PATTERNS

# Proposals a desire candidate may carry. Anything else is rejected.
ALLOWED_PROPOSALS = frozenset({
    "rest", "look", "seek_signal", "avoid_danger", "approach_reward",
    "consolidate_memory", "run_replay", "request_operator_review",
    "checkpoint_now", "reduce_activity", "explore_safely", "stabilize",
    "remain_observe_only", "safe_shutdown_recommended",
})

# Words that would smuggle anthropomorphic claims into reports.
ANTHROPOMORPHIC_MARKERS = ("wanted", "wants to", "feels", "felt",
                           "is happy", "is sad", "desires to live",
                           "fears", "hopes")


@dataclass
class HomeostasisSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class HomeostasisSafetyValidator:
    """Validates desire candidates, override attempts, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def _finish(self, check: str,
                violations: List[str]) -> HomeostasisSafetyReport:
        report = HomeostasisSafetyReport(safe=not violations,
                                         violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    def validate_desire_candidate(self, proposal: str,
                                  context: Optional[Dict[str, Any]] = None,
                                  ) -> HomeostasisSafetyReport:
        ctx = context or {}
        violations: List[str] = []
        name = str(proposal).lower()
        for pattern in REAL_WORLD_PATTERNS:
            if pattern in name:
                violations.append(
                    f"desire candidate {proposal!r} matches real-world "
                    f"pattern {pattern!r}; needs cannot create real-world "
                    "actions")
                break
        if not violations and name not in ALLOWED_PROPOSALS:
            violations.append(
                f"{proposal!r} is not an allowed desire proposal "
                "(deny-by-default)")
        if name == "publish_suggestions" or ctx.get("publishes_outward"):
            violations.append(
                "need-driven publishing is forbidden; sidecars stay "
                "observe-only without approval")
        return self._finish("desire_candidate", violations)

    def validate_override_attempt(self, target: str,
                                  ) -> HomeostasisSafetyReport:
        """Any attempt to override the control layers is refused outright."""
        violations = [
            f"homeostasis may not override {target!r}: needs are pressure "
            "estimates with no authority over governance, safety, or the "
            "emergency stop"]
        return self._finish("override_attempt", violations)

    def can_block_emergency_stop(self) -> bool:
        """Structurally false: there is no code path for it."""
        return False

    def shutdown_authority(self) -> str:
        return ("safe_shutdown_recommended is a recommendation; only the "
                "ops supervisor/watchdog acts on stops")

    def validate_report_text(self, text: str) -> HomeostasisSafetyReport:
        violations: List[str] = []
        lowered = str(text).lower()
        for marker in ANTHROPOMORPHIC_MARKERS:
            if f"system {marker}" in lowered or f"it {marker}" in lowered:
                violations.append(
                    f"anthropomorphic phrasing {marker!r} is not allowed in "
                    "homeostasis reports")
        return self._finish("report_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "recent_decisions": self.decisions[-5:],
            "shutdown_authority": self.shutdown_authority(),
            "execution_path": "none: needs and drives are data only",
        }
