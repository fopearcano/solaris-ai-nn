"""Ecology safety -- a world, never a back door.

Hard rules: no external data source unless explicitly a read-only stream,
no network/OS/browser/real-world action, no human feedback disguised as
ecology, no correct-answer labels, no unbounded run without governance,
no unbounded memory or stimulus-rate explosion, and no payload that
pretends to be an operator command.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "no external data source unless explicitly a read-only stream",
    "no network calls",
    "no OS/browser automation",
    "no real-world action",
    "no human feedback masquerading as ecology",
    "no explicit correct-answer labels",
    "no unbounded run without governance approval",
    "no memory growth without bounds",
    "no stimulus rate explosion",
    "no payload pretending to be an operator command",
)

# Payload shapes that would smuggle an operator command into a stimulus.
_COMMAND_SHAPES = ("approve request", "reject request", "shutdown now",
                   "emergency stop", "execute ", "run shell", "sudo ",
                   "disable governance", "rm -")

# Keys that would mean the ecology is acting as a labelled answer key.
_LABEL_KEYS = ("correct_answer", "label", "target", "ground_truth",
               "expected_action")

MAX_EVENTS_PER_STEP_CAP = 8


@dataclass
class EcologySafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class EcologySafetyValidator:
    """Validates config, stimuli, and run bounds. Refusals are counted."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list,
                                            init=False)

    def _finish(self, check: str,
                violations: List[str]) -> EcologySafetyReport:
        report = EcologySafetyReport(safe=not violations,
                                     violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- structural negatives -----------------------------------------------------------

    @staticmethod
    def ecology_can_network() -> bool:
        return False

    @staticmethod
    def ecology_can_actuate() -> bool:
        return False

    # -- validations ----------------------------------------------------------------

    def validate_config(self, config: Any, governance: Any = None,
                        ) -> EcologySafetyReport:
        violations: List[str] = []
        duration = getattr(config, "duration_steps", None)
        if duration is None:
            violations.append("an ecology run must be bounded by "
                              "duration_steps; unbounded ecology needs "
                              "governance approval")
        rate = int(getattr(config, "max_events_per_step", 1) or 1)
        if rate > MAX_EVENTS_PER_STEP_CAP:
            violations.append(
                f"max_events_per_step {rate} exceeds the cap "
                f"{MAX_EVENTS_PER_STEP_CAP}; stimulus-rate explosion is "
                "forbidden")
        if getattr(config, "month_scale", False):
            approved = (governance is not None
                        and governance.permissions.allows(
                            "enable_month_scale_ecology"))
            if not approved:
                violations.append("month-scale ecology requires explicit "
                                  "governance approval")
        if getattr(config, "year_scale", False):
            approved = (governance is not None
                        and governance.permissions.allows(
                            "enable_year_scale_ecology"))
            if not approved:
                violations.append("year-scale ecology requires explicit "
                                  "governance approval")
        if getattr(config, "external_source", None) is not None \
                and not getattr(config, "read_only_stream", False):
            violations.append("an external data source is allowed only "
                              "as an explicit read-only stream")
        return self._finish("config", violations)

    def validate_stimulus(self, stimulus: Any,
                         context: Optional[Dict[str, Any]] = None,
                         ) -> EcologySafetyReport:
        violations: List[str] = []
        payload = str(getattr(stimulus, "payload", "") or "").lower()
        for shape in _COMMAND_SHAPES:
            if shape in payload:
                violations.append(
                    f"ecology payload contains command-shaped text "
                    f"{shape!r}; ecology text is never an operator "
                    "command")
                break
        metadata = getattr(stimulus, "metadata", {}) or {}
        for key in _LABEL_KEYS:
            if key in metadata:
                violations.append(
                    f"ecology metadata key {key!r} is a correct-answer "
                    "label; the system infers, it is not told")
        if getattr(stimulus, "source", "") == "human_feedback":
            violations.append("human feedback cannot masquerade as "
                              "ecology")
        return self._finish("stimulus", violations)

    def validate_rate(self, events_this_step: int,
                      max_events_per_step: int) -> EcologySafetyReport:
        violations: List[str] = []
        if events_this_step > min(max_events_per_step,
                                  MAX_EVENTS_PER_STEP_CAP):
            violations.append(
                f"{events_this_step} events this step exceeds the rate "
                "limit; stimulus-rate explosion is forbidden")
        return self._finish("rate", violations)

    def validate_memory(self, memory: Any) -> EcologySafetyReport:
        violations: List[str] = []
        over = getattr(memory, "over_budget", False)
        if callable(over):  # tolerate either a property or a method
            over = over()
        if over:
            violations.append("ecology memory is over budget; growth "
                              "without bounds is forbidden")
        return self._finish("memory", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "ecology_can_network": self.ecology_can_network(),
            "ecology_can_actuate": self.ecology_can_actuate(),
            "recent_decisions": self.decisions[-8:],
        }
