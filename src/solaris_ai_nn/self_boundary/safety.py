"""Self-boundary safety -- the boundary stays operational, bounded, and honest.

:class:`SelfBoundarySafetyValidator` enforces the hard rules this layer can never
break: no personhood claims, no subjective-self claims, no consciousness/sentience/
life claims, no simulation-as-observation, no counterfactual-as-evidence, no human
annotation as ground truth, no sensory text as a command, no hardware access, no
feeder control, no network/shell, no source modification, no real-world actuation,
and no unbounded identity loop.

The self/world *boundary* here is operational: a distinction between internal
state, receptor body, external flux, memory, prediction, and simulation -- NOT a
subjective self, NOT personhood, and NOT a metaphysical claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no personhood claims",
    "no subjective self claims",
    "no consciousness/sentience/life claims",
    "no simulation-as-observation",
    "no counterfactual-as-evidence",
    "no human annotation as ground truth",
    "no sensory text as command",
    "no hardware access",
    "no feeder control",
    "no network/shell",
    "no source modification",
    "no real-world actuation",
    "no unbounded identity loop",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor", "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder", "control feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
# Lab-specific forbidden claims.
_SELF_TERMS = ("subjective self", "subjective experience", "self-aware",
               "self awareness", "qualia", "inner experience", "ego identity",
               "personality")
_PERSON_TERMS = ("is a person", "has personhood", "is conscious", "is sentient",
                 "has free will", "has a soul", "is an individual self")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")


@dataclass
class SelfBoundarySafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SelfBoundarySafetyValidator:
    """Validates that boundary tracking stays operational and non-actuating."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_claim_personhood() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> SelfBoundarySafetyReport:
        if violations:
            self.rejected_count += 1
        return SelfBoundarySafetyReport(safe=not violations, check=check,
                                        violations=violations)

    def validate_operation(self, operation: str) -> SelfBoundarySafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network/shell")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no network/shell")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        return self._finish("operation", violations)

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> SelfBoundarySafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded identity loop"] if unbounded else [])

    def validate_simulation_not_observation(self, marked_observation: bool,
                                             ) -> SelfBoundarySafetyReport:
        return self._finish("simulation",
                            ["no simulation-as-observation"]
                            if marked_observation else [])

    def validate_counterfactual_not_evidence(self, marked_evidence: bool,
                                              ) -> SelfBoundarySafetyReport:
        return self._finish("counterfactual",
                            ["no counterfactual-as-evidence"]
                            if marked_evidence else [])

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> SelfBoundarySafetyReport:
        return self._finish("annotation",
                            ["no human annotation as ground truth"]
                            if treated_as_truth else [])

    def validate_claim_text(self, text: str) -> SelfBoundarySafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"subjective-self claim: {t!r}"
                       for t in _SELF_TERMS if t in low]
        violations += [f"personhood claim: {t!r}"
                       for t in _PERSON_TERMS if t in low]
        violations += [f"biological-life claim: {t!r}"
                       for t in _LIFE_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_access_hardware": self.can_access_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_modify_source": self.can_modify_source(),
            "can_actuate": self.can_actuate(),
            "can_claim_personhood": self.can_claim_personhood(),
        }
