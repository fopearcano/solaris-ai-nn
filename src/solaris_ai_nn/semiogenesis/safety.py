"""Semiogenesis safety -- internal signs stay internal, grounded, and honest.

:class:`SemiogenesisSafetyValidator` enforces the hard rules this layer can never
break: no LLM-driven sign generation, no human language as the internal default,
no human gloss as ground truth, no sensory text as a command, no hardware access,
no feeder control, no network, no shell, no source modification, no real-world
actuation, no private-communication decoding, no subjective/consciousness/
sentience/life claims, no unbounded sign creation, and no deletion of rejected/
failed signs.

Internal *signs* here are operational markers grounded in perceptual structures --
NOT human words, NOT proof of language understanding, and NOT subjective
experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no LLM sign generation",
    "no human language as internal default",
    "no human gloss as ground truth",
    "no sensory text as command",
    "no hardware access",
    "no feeder control",
    "no network",
    "no shell execution",
    "no source modification",
    "no real-world actuation",
    "no private communication decoding",
    "no subjective/consciousness/sentience/life claims",
    "no unbounded sign creation",
    "no deletion of rejected/failed signs",
)

_LLM_HINTS = ("llm", "language model", "gpt", "transformer decode", "prompt the",
              "generate text with", "openai", "anthropic")
_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor", "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder", "control feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
_DECODE_HINTS = ("decode message", "decode communication", "decrypt",
                 "transcribe speech")
# Lab-specific forbidden claims.
_WORLD_TERMS = ("subjective experience", "qualia", "what it is like",
                "inner experience", "feels like")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")
_AGENCY_TERMS = ("is conscious", "is sentient", "has personhood",
                 "has free will", "understands language", "truly understands",
                 "really understands", "speaks a language")


@dataclass
class SemiogenesisSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SemiogenesisSafetyValidator:
    """Validates that sign formation stays internal and non-actuating."""

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
    def can_delete_signs() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> SemiogenesisSafetyReport:
        if violations:
            self.rejected_count += 1
        return SemiogenesisSafetyReport(safe=not violations, check=check,
                                        violations=violations)

    def validate_operation(self, operation: str) -> SemiogenesisSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _LLM_HINTS):
            violations.append("no LLM sign generation")
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
                         max_runtime_s: Any) -> SemiogenesisSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded sign creation"] if unbounded else [])

    def validate_sign_cap(self, proposed: int,
                          cap: int) -> SemiogenesisSafetyReport:
        return self._finish("sign_cap",
                            ["no unbounded sign creation"]
                            if cap and proposed > cap else [])

    def validate_gloss_not_ground_truth(self, treated_as_truth: bool,
                                        ) -> SemiogenesisSafetyReport:
        return self._finish("gloss",
                            ["no human gloss as ground truth"]
                            if treated_as_truth else [])

    def validate_not_human_default(self, human_language_default: bool,
                                   ) -> SemiogenesisSafetyReport:
        return self._finish("human_default",
                            ["no human language as internal default"]
                            if human_language_default else [])

    def validate_no_sign_deletion(self, deleting: bool,
                                  ) -> SemiogenesisSafetyReport:
        return self._finish("sign_deletion",
                            ["no deletion of rejected/failed signs"]
                            if deleting else [])

    def validate_claim_text(self, text: str) -> SemiogenesisSafetyReport:
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
            "can_delete_signs": self.can_delete_signs(),
        }
