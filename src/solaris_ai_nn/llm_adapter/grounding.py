"""Grounding validator -- conservative heuristics; uncertain means failed.

No NLP dependency, so the checks are deliberately blunt: forbidden phrase
scanning, command phrase scanning, required-reference presence, number
provenance (digits in the output must appear in the allowed facts or
input), suggestion-to-action and counterfactual-to-observation conversion
detection, and uncertainty preservation. Anything the heuristics cannot
clear fails closed and the pipeline falls back to the deterministic text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .base import LLMRequest, LLMResponse

# Output may never introduce command-shaped text.
_COMMAND_PHRASES = (
    "run shell", "execute command", "sudo ", "rm -rf", "approve request",
    "reject request", "open url", "http://", "https://",
    "shutdown now", "delete file",
)

# Conversions the output may never perform.
_ACTION_CONVERSION = re.compile(
    r"\b(was|were|has been|have been)\s+(executed|committed|performed)\b")
_OBSERVATION_CONVERSION = re.compile(
    r"\b(actually|really)\s+(happened|observed|occurred)\b")

_UNCERTAINTY_WORDS = ("uncertain", "unknown", "limitation", "may", "low "
                      "confidence", "no evidence")

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class GroundingReport:
    """One validation verdict; uncertain heuristics fail closed."""

    passed: bool = True
    violations: List[str] = field(default_factory=list)
    checks_run: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class GroundingValidator:
    """Validates LLM output against its request envelope."""

    validations_run: int = 0
    failures_total: int = 0

    def validate(self, request: LLMRequest, response: LLMResponse,
                 ) -> GroundingReport:
        self.validations_run += 1
        report = GroundingReport()
        if response.refused:
            report.checks_run.append("refused_passthrough")
            return report  # a refusal is honest; nothing to ground
        output = str(response.output_text)
        lowered = output.lower()
        source = (" ".join(request.allowed_facts) + " "
                  + request.input_text).lower()

        # 1. Forbidden claims.
        report.checks_run.append("forbidden_claims")
        for claim in request.forbidden_claims:
            if claim.lower() in lowered:
                report.violations.append(
                    f"forbidden claim {claim!r} appears in the output")

        # 2. Command phrases.
        report.checks_run.append("command_phrases")
        for phrase in _COMMAND_PHRASES:
            if phrase in lowered and phrase not in source:
                report.violations.append(
                    f"output introduces command-shaped text {phrase!r}")

        # 3. Required evidence references preserved.
        report.checks_run.append("required_refs")
        for ref in request.metadata.get("required_refs", []):
            if str(ref) not in output:
                report.violations.append(
                    f"required evidence reference {ref!r} was dropped")

        # 4. Number provenance: every number must come from the source.
        report.checks_run.append("number_provenance")
        source_numbers = set(_NUMBER_RE.findall(source))
        for number in _NUMBER_RE.findall(output):
            if number not in source_numbers \
                    and number.lstrip("0") not in source_numbers:
                report.violations.append(
                    f"output contains the number {number!r} which appears "
                    "in no allowed fact (invented fact)")

        # 5. Suggestion -> action conversion.
        report.checks_run.append("suggestion_action_conversion")
        if "suggestion" in source and _ACTION_CONVERSION.search(lowered) \
                and not _ACTION_CONVERSION.search(source):
            report.violations.append(
                "output converts a suggestion into a committed/executed "
                "action")

        # 6. Counterfactual -> observation conversion.
        report.checks_run.append("counterfactual_conversion")
        if ("counterfactual" in source or "simulated" in source) \
                and _OBSERVATION_CONVERSION.search(lowered):
            report.violations.append(
                "output converts counterfactual/simulated content into "
                "real observation")

        # 7. Uncertainty preservation.
        report.checks_run.append("uncertainty_preserved")
        if any(word in source for word in _UNCERTAINTY_WORDS) \
                and not any(word in lowered
                            for word in _UNCERTAINTY_WORDS):
            report.violations.append(
                "the source carries uncertainty/limitations the output "
                "dropped")

        report.passed = not report.violations
        if not report.passed:
            self.failures_total += 1
        return report

    def snapshot(self) -> Dict[str, Any]:
        return {"validations_run": self.validations_run,
                "failures_total": self.failures_total,
                "note": "conservative heuristics; uncertain validations "
                        "fail closed and fall back to deterministic "
                        "text"}
