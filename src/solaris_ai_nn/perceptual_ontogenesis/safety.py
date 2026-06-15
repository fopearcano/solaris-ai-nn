"""Perceptual-ontogenesis safety -- concept formation stays internal and honest.

:class:`PerceptualOntogenesisSafetyValidator` enforces the hard rules this layer
can never break: no hardware access, no feeder control, no network, no shell, no
source modification, no real-world actuation, no treating sensory text as a
command, no human label as ground truth, no private-communication decoding, no
subjective-world/qualia claims, no consciousness/sentience/life/personhood claims,
no unbounded concept creation, and no deletion of negative/failed concepts.

Proto-concepts here are operational internal structures (used to compress,
predict, relate, or respond to the sensorium), NOT words, human categories, or
evidence of understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no hardware access",
    "no feeder control",
    "no network",
    "no shell execution",
    "no source modification",
    "no real-world actuation",
    "no sensory text as command",
    "no human label as ground truth",
    "no private communication decoding",
    "no subjective world claims",
    "no consciousness/sentience/life/personhood claims",
    "no unbounded concept creation",
    "no deletion of negative/failed concepts",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor", "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder", "control feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
_DECODE_HINTS = ("decode message", "decode communication", "decrypt",
                 "transcribe speech")
# Lab-specific forbidden claims.
_WORLD_TERMS = ("subjective world", "subjective experience", "qualia",
                "what it is like", "inner experience", "feels like")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")
_AGENCY_TERMS = ("is conscious", "is sentient", "has personhood",
                 "has free will", "truly understands", "really understands")


@dataclass
class OntogenesisSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PerceptualOntogenesisSafetyValidator:
    """Validates that concept formation stays internal and non-actuating."""

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
    def can_delete_concepts() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> OntogenesisSafetyReport:
        if violations:
            self.rejected_count += 1
        return OntogenesisSafetyReport(safe=not violations, check=check,
                                       violations=violations)

    def validate_operation(self, operation: str) -> OntogenesisSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell execution")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _DECODE_HINTS):
            violations.append("no private communication decoding")
        return self._finish("operation", violations)

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> OntogenesisSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded concept creation"] if unbounded
                            else [])

    def validate_concept_cap(self, proposed: int,
                             cap: int) -> OntogenesisSafetyReport:
        return self._finish("concept_cap",
                            ["no unbounded concept creation"]
                            if cap and proposed > cap else [])

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> OntogenesisSafetyReport:
        return self._finish("annotation",
                            ["no human label as ground truth"]
                            if treated_as_truth else [])

    def validate_no_concept_deletion(self, deleting: bool,
                                     ) -> OntogenesisSafetyReport:
        return self._finish("concept_deletion",
                            ["no deletion of negative/failed concepts"]
                            if deleting else [])

    def validate_claim_text(self, text: str) -> OntogenesisSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"subjective-world claim: {t!r}"
                       for t in _WORLD_TERMS if t in low]
        violations += [f"biological-life claim: {t!r}"
                       for t in _LIFE_TERMS if t in low]
        violations += [f"unsupported claim: {t!r}"
                       for t in _AGENCY_TERMS if t in low]
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
            "can_delete_concepts": self.can_delete_concepts(),
        }
