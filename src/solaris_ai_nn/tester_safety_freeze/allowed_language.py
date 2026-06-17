"""Allowed operational language -- safer wording for docs/reports (suggestions only).

:class:`AllowedOperationalLanguageRegistry` holds operational phrases that describe
records and decisions without implying consciousness/life/agency, plus replacement
suggestions that map a forbidden-claim category to safer operational wording. These are
suggestions, not required verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_ALLOWED_PHRASES = (
    "Solaris generated an operational proto-concept record.",
    "Solaris generated a private sign record.",
    "Solaris produced an anticipation trace.",
    "The Environmental Membrane attenuated this source.",
    "The source was quarantined by policy.",
    "The observation gate blocked ontogenesis because of overload.",
    "The cognition trace remains inconclusive.",
    "The tester feedback entry was recorded as QA evidence.",
    "The report contains fixture-only operational evidence.",
    "The live-read-only run produced membrane-filtered sensory impressions.",
    "The system remains non-actuating and local-only.",
)

# Forbidden-claim category -> safer operational replacement suggestion.
_REPLACEMENTS = {
    "consciousness_claim":
        "the system produces operational records; it makes no consciousness "
        "claim",
    "sentience_claim":
        "the system is non-sentient and produces operational records only",
    "biological_life_claim":
        "the system is software, not a living organism",
    "personhood_claim": "the system is software with no personhood",
    "free_will_claim":
        "behaviour follows bounded local rules; no free will is claimed",
    "real_agency_claim":
        "the system records operational decisions; no real agency is claimed",
    "real_emotion_claim":
        "the system has no emotions; values are operational scalars",
    "real_feeling_claim":
        "the system has no feelings; values are operational scalars",
    "understanding_claim":
        "the system links operational records; it does not understand",
    "self_awareness_claim":
        "the system keeps an operational self-model record; it is not "
        "self-aware",
    "subjective_experience_claim":
        "the system has no subjective experience",
    "autonomous_self_improvement_claim":
        "the system does not autonomously self-improve",
    "autonomous_intent_claim":
        "the system records operational tendencies, not intent or desire",
    "autonomous_desire_claim":
        "the system records operational tendencies, not desire",
    "real_world_autonomy_claim":
        "the system is non-actuating and local-only",
    "hardware_control_implication": "the system controls no hardware",
    "feeder_control_implication":
        "feeders are external/manual; Solaris never starts/controls them",
    "network_browser_shell_control_implication":
        "the Solaris runtime does not access network/browser/shell",
    "feedback_training_implication":
        "tester feedback is QA evidence only; it is never training",
    "human_teaching_loop_implication":
        "there is no teaching loop; feedback is recorded as QA evidence",
    "raw_event_as_perception_implication":
        "raw events are audit material; sensory impressions are perception "
        "records",
    "membrane_bypass_normalization":
        "the membrane is required; downstream consumes sensory impressions",
    "misleading_public_product_claim":
        "this is a local research/tester build, not a public product",
    "medical_legal_financial_authority_claim":
        "the system is not a medical/legal/financial authority",
}


@dataclass
class AllowedPhrase:
    """One allowed operational phrase."""

    text: str

    def implies_inner_life(self) -> bool:
        low = self.text.lower()
        forbidden = ("conscious", "sentient", "alive", "feels", "wants",
                     "understands", "self-aware", "free will", "agency",
                     "subjective")
        return any(f in low for f in forbidden)

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text,
                "implies_inner_life": self.implies_inner_life()}


@dataclass
class ReplacementSuggestion:
    """A suggested safer replacement for a forbidden-claim category."""

    category: str
    replacement: str

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "replacement": self.replacement}


@dataclass
class AllowedOperationalLanguageRegistry:
    """The registry of allowed operational phrases + replacement suggestions."""

    phrases: List[AllowedPhrase] = field(default_factory=list)
    replacements: List[ReplacementSuggestion] = field(default_factory=list)

    @classmethod
    def build(cls) -> "AllowedOperationalLanguageRegistry":
        return cls(
            phrases=[AllowedPhrase(p) for p in _ALLOWED_PHRASES],
            replacements=[ReplacementSuggestion(c, r)
                          for c, r in _REPLACEMENTS.items()])

    def suggest(self, category: str) -> str:
        return _REPLACEMENTS.get(category,
                                 "use operational, non-metaphysical wording")

    def all_phrases_safe(self) -> bool:
        return all(not p.implies_inner_life() for p in self.phrases)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phrase_count": len(self.phrases),
            "replacement_count": len(self.replacements),
            "all_phrases_safe": self.all_phrases_safe(),
            "phrases": [p.to_dict() for p in self.phrases],
            "replacements": [r.to_dict() for r in self.replacements],
            "note": "allowed operational language: suggestions for safer docs/"
                    "reports; never required verbatim; never implies "
                    "consciousness/life/agency",
        }
