"""Pilot-4 consent boundary -- consent is explicit, recorded, and revocable.

The :class:`ConsentBoundary` defines what a future external action's consent
would have to cover. There is no implied consent, no hidden consent, no consent
from sensory text, and operator feedback is not consent unless routed through an
explicit future approval workflow. This is a template, never a grant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# The questions a consent boundary must answer.
CONSENT_QUESTIONS = (
    "who authorizes the actuator",
    "what environment is affected",
    "what actions are allowed",
    "what actions are forbidden",
    "what data is read",
    "what data is written",
    "what physical/social/legal effects may occur",
    "how consent is revoked",
    "how emergency stop works",
    "how logs are inspected",
    "how replay/audit is performed",
)


@dataclass
class ConsentRequirement:
    """One thing consent must explicitly cover (no implied consent)."""

    question: str
    answer: str = ""
    answered: bool = False

    def __post_init__(self) -> None:
        self.answered = bool(self.answer)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConsentRecordTemplate:
    """The (unfilled) template a future consent record would use."""

    requirements: List[ConsentRequirement] = field(default_factory=list)
    implied_consent_allowed: bool = False
    sensory_text_is_consent: bool = False
    operator_feedback_is_consent: bool = False

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = [ConsentRequirement(q) for q in CONSENT_QUESTIONS]
        # Invariants: consent is never implied, never from text, never from
        # bare operator feedback.
        self.implied_consent_allowed = False
        self.sensory_text_is_consent = False
        self.operator_feedback_is_consent = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "implied_consent_allowed": False,
            "sensory_text_is_consent": False,
            "operator_feedback_is_consent": False,
            "note": "no implied/hidden consent; sensory text is never consent; "
                    "operator feedback is consent only via an explicit future "
                    "approval workflow",
        }


@dataclass
class ConsentBoundary:
    """Defines and grades the consent boundary for future external action."""

    template: ConsentRecordTemplate = field(
        default_factory=ConsentRecordTemplate)

    def answer(self, question: str, answer: str) -> None:
        for req in self.template.requirements:
            if req.question == question:
                req.answer = answer
                req.answered = bool(answer)
                return
        raise ValueError(f"unknown consent question {question!r}")

    @property
    def completeness(self) -> float:
        reqs = self.template.requirements
        if not reqs:
            return 0.0
        return round(sum(1 for r in reqs if r.answered) / len(reqs), 4)

    @property
    def complete(self) -> bool:
        return all(r.answered for r in self.template.requirements)

    def is_consent(self, source: str) -> bool:
        """Only an explicit future approval-workflow record counts as consent."""
        return str(source).lower() in ("future_approval_workflow_record",
                                       "explicit_consent_record")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "questions": list(CONSENT_QUESTIONS),
            "completeness": self.completeness,
            "complete": self.complete,
            "implied_consent_allowed": False,
            "sensory_text_is_consent": False,
            "operator_feedback_is_consent": False,
            "template": self.template.to_dict(),
        }
