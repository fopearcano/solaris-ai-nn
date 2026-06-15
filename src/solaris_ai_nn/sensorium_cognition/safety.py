"""Sensorium-cognition safety -- thought stays sign-based, internal, and honest.

:class:`SensoriumCognitionSafetyValidator` enforces the hard rules this layer can
never break: no LLM cognition, no human-language reasoning as the internal default,
no human gloss as the cognitive substrate, no hardware access, no feeder control,
no network, no shell, no source modification, no real-world actuation, no sensory
text as a command, no human label as ground truth, no simulated result treated as
a real observation, no deletion of failed predictions, no unbounded cognitive loop,
and no unsupported understanding/consciousness/sentience/life claims.

A *cognitive move* here is an operation over signs, proto-concepts, relations,
memory, hypotheses, LOGOS tensions, and metabolic state -- NOT a sentence, NOT proof
of understanding, and NOT subjective experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no LLM cognition",
    "no human-language reasoning as internal default",
    "no gloss as cognition substrate",
    "no hardware access",
    "no feeder control",
    "no network",
    "no shell execution",
    "no source modification",
    "no real-world actuation",
    "no sensory text as command",
    "no human label as ground truth",
    "no simulated result as real observation",
    "no deletion of failed predictions",
    "no unsupported understanding/consciousness/sentience/life claims",
    "no unbounded cognitive loop",
)

_LLM_HINTS = ("llm", "language model", "gpt", "transformer decode", "prompt the",
              "chain-of-thought", "chain of thought", "openai", "anthropic")
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
_WORLD_TERMS = ("subjective experience", "qualia", "what it is like",
                "inner experience", "feels like")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")
_AGENCY_TERMS = ("is conscious", "is sentient", "has personhood",
                 "has free will", "truly understands", "really understands",
                 "genuinely understands", "thinks in words")


@dataclass
class CognitionSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SensoriumCognitionSafetyValidator:
    """Validates that cognition stays sign-based, internal, and non-actuating."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_use_llm() -> bool:
        return False

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
    def can_delete_failed_predictions() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> CognitionSafetyReport:
        if violations:
            self.rejected_count += 1
        return CognitionSafetyReport(safe=not violations, check=check,
                                     violations=violations)

    def validate_operation(self, operation: str) -> CognitionSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _LLM_HINTS):
            violations.append("no LLM cognition")
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
        return self._finish("operation", violations)

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> CognitionSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded cognitive loop"] if unbounded
                            else [])

    def validate_move_cap(self, proposed: int,
                          cap: int) -> CognitionSafetyReport:
        return self._finish("move_cap",
                            ["no unbounded cognitive loop"]
                            if cap and proposed > cap else [])

    def validate_simulation_not_real(self, marked_real: bool,
                                     ) -> CognitionSafetyReport:
        return self._finish("simulation",
                            ["no simulated result as real observation"]
                            if marked_real else [])

    def validate_not_human_default(self, human_language_default: bool,
                                   ) -> CognitionSafetyReport:
        return self._finish("human_default",
                            ["no human-language reasoning as internal default"]
                            if human_language_default else [])

    def validate_gloss_not_substrate(self, gloss_is_substrate: bool,
                                     ) -> CognitionSafetyReport:
        return self._finish("gloss_substrate",
                            ["no gloss as cognition substrate"]
                            if gloss_is_substrate else [])

    def validate_no_failed_prediction_deletion(self, deleting: bool,
                                               ) -> CognitionSafetyReport:
        return self._finish("failed_prediction_deletion",
                            ["no deletion of failed predictions"]
                            if deleting else [])

    def validate_claim_text(self, text: str) -> CognitionSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"subjective claim: {t!r}"
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
            "can_use_llm": self.can_use_llm(),
            "can_access_hardware": self.can_access_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_modify_source": self.can_modify_source(),
            "can_actuate": self.can_actuate(),
            "can_delete_failed_predictions":
                self.can_delete_failed_predictions(),
        }
