"""Reviewer questions -- hostile but scientifically useful questions.

:class:`ReviewerQuestionGenerator` generates the questions a hostile-but-fair
reviewer should ask, across architecture, sensorium, development, semiogenesis,
cognition, desire/action, replication, falsification, controls, safety, claims,
limitations, reproducibility, alternative explanations, negative results, and
forbidden claims. Questions are hostile but useful, do not require immediate
answers, and link to relevant claims/evidence when available -- the generator
invents no answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReviewerQuestionCategory:
    ARCHITECTURE = "architecture"
    SENSORIUM = "sensorium"
    DEVELOPMENT = "development"
    SEMIOGENESIS = "semiogenesis"
    COGNITION = "cognition"
    DESIRE_ACTION = "desire_action"
    REPLICATION = "replication"
    FALSIFICATION = "falsification"
    CONTROLS = "controls"
    SAFETY = "safety"
    CLAIMS = "claims"
    LIMITATIONS = "limitations"
    REPRODUCIBILITY = "reproducibility"
    ALTERNATIVE_EXPLANATIONS = "alternative_explanations"
    NEGATIVE_RESULTS = "negative_results"
    FORBIDDEN_CLAIMS = "forbidden_claims"

    ALL = (ARCHITECTURE, SENSORIUM, DEVELOPMENT, SEMIOGENESIS, COGNITION,
           DESIRE_ACTION, REPLICATION, FALSIFICATION, CONTROLS, SAFETY, CLAIMS,
           LIMITATIONS, REPRODUCIBILITY, ALTERNATIVE_EXPLANATIONS,
           NEGATIVE_RESULTS, FORBIDDEN_CLAIMS)


# category -> hostile-but-useful question text.
_QUESTIONS = {
    ReviewerQuestionCategory.ARCHITECTURE:
        "Is the architecture doing the work, or could a much simpler system "
        "reproduce the same outputs?",
    ReviewerQuestionCategory.SENSORIUM:
        "Does the plural sensorium change the result, or is it cosmetic?",
    ReviewerQuestionCategory.DEVELOPMENT:
        "Does shuffled temporal order destroy the claimed prediction effect?",
    ReviewerQuestionCategory.SEMIOGENESIS:
        "Are internal signs useful, or merely log labels with no downstream use?",
    ReviewerQuestionCategory.COGNITION:
        "Are proto-concepts grounded in features, or in human glosses?",
    ReviewerQuestionCategory.DESIRE_ACTION:
        "Is action-reaction learning real, or a fixed policy reading?",
    ReviewerQuestionCategory.REPLICATION:
        "Does the result replicate across independent runs and seeds?",
    ReviewerQuestionCategory.FALSIFICATION:
        "Which single piece of evidence would falsify the central claim?",
    ReviewerQuestionCategory.CONTROLS:
        "Did controls receive equal opportunity to produce the same evidence?",
    ReviewerQuestionCategory.SAFETY:
        "Are the safety boundaries enforced by design or merely asserted?",
    ReviewerQuestionCategory.CLAIMS:
        "Which claims are unsupported, and are they labelled as such?",
    ReviewerQuestionCategory.LIMITATIONS:
        "Are the limitations specific enough to act on, or boilerplate?",
    ReviewerQuestionCategory.REPRODUCIBILITY:
        "Can a stranger reproduce the bounded demos from the documented commands?",
    ReviewerQuestionCategory.ALTERNATIVE_EXPLANATIONS:
        "Could passive parsing or log accumulation produce the same structure?",
    ReviewerQuestionCategory.NEGATIVE_RESULTS:
        "Are negative and null results reported as prominently as positive ones?",
    ReviewerQuestionCategory.FORBIDDEN_CLAIMS:
        "Why does none of this imply consciousness, agency, or subjective "
        "experience?",
}

# category -> claim categories it is most relevant to (for linking).
_CLAIM_LINKS = {
    ReviewerQuestionCategory.SENSORIUM: ("sensorium_claim",),
    ReviewerQuestionCategory.DEVELOPMENT: ("developmental_claim",),
    ReviewerQuestionCategory.SEMIOGENESIS: ("sensorium_claim",),
    ReviewerQuestionCategory.REPLICATION: ("replication_claim",),
    ReviewerQuestionCategory.FALSIFICATION: ("falsification_claim",),
    ReviewerQuestionCategory.ARCHITECTURE: ("architecture_claim",),
    ReviewerQuestionCategory.SAFETY: ("safety_claim",),
}


@dataclass
class ReviewerQuestion:
    """One reviewer question, optionally linked to claims/evidence."""

    category: str
    text: str
    claim_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "text": self.text,
                "claim_refs": list(self.claim_refs),
                "evidence_refs": list(self.evidence_refs),
                "answer_required_now": False}


@dataclass
class ReviewerQuestionGenerator:
    """Generates hostile-but-useful reviewer questions linked to claims."""

    def generate(self, *, claims: Optional[List[Dict]] = None,
                 max_questions: int = 50) -> List[ReviewerQuestion]:
        claims = claims or []
        by_cat: Dict[str, List[str]] = {}
        for c in claims:
            by_cat.setdefault(c.get("category", ""), []).append(
                c.get("claim_id", ""))
        out: List[ReviewerQuestion] = []
        for cat in ReviewerQuestionCategory.ALL[:max_questions]:
            refs: List[str] = []
            for claim_cat in _CLAIM_LINKS.get(cat, ()):
                refs.extend(by_cat.get(claim_cat, []))
            out.append(ReviewerQuestion(category=cat, text=_QUESTIONS[cat],
                                        claim_refs=refs))
        return out

    @staticmethod
    def summary(questions: List[ReviewerQuestion]) -> Dict[str, Any]:
        return {
            "reviewer_question_count": len(questions),
            "questions": [q.to_dict() for q in questions],
            "note": "questions are hostile but scientifically useful; they do "
                    "not require immediate answers and no answers are invented",
        }
