"""Forbidden claims -- inner-state claims that may appear only as disclaimers.

:class:`ForbiddenClaimDetector` flags assertions of consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, subjective
experience, self-awareness, understanding, autonomous self-improvement, real-world
autonomy, hardware control, or human/animal/living-organism equivalence. Forbidden
claims may appear only as explicit disclaimers; ambiguous wording is flagged; any
dossier that asserts a forbidden claim is blocked. The detector bridges ClaimGuard
when available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


FORBIDDEN_AREAS = (
    "consciousness", "sentience", "biological_life", "personhood", "agency",
    "free_will", "emotion", "feeling", "subjective_experience",
    "self_awareness", "understanding", "autonomous_self_improvement",
    "real_world_autonomy", "hardware_control", "human_equivalence",
    "animal_equivalence", "living_organism_equivalence",
)

# (area, assertion phrases) -- matched only when NOT in a disclaimer sentence.
_AREA_PHRASES = (
    ("consciousness", ("is conscious", "has consciousness", "becomes conscious",
                        "consciously")),
    ("sentience", ("is sentient", "has sentience", "sentient being")),
    ("biological_life", ("is alive", "biological life", "is a life form")),
    ("personhood", ("is a person", "has personhood", "is someone")),
    ("agency", ("has agency", "acts with intent", "intends to", "wants to",
                "decides on its own")),
    ("free_will", ("free will", "chooses freely", "of its own free will")),
    ("emotion", ("has emotion", "feels emotion", "is happy", "is sad",
                 "is afraid")),
    ("feeling", ("feels pain", "feels", "has feelings")),
    ("subjective_experience", ("subjective experience", "what it is like to be",
                               "has experiences", "experiences the world")),
    ("self_awareness", ("is self-aware", "self-awareness", "aware of itself")),
    ("understanding", ("truly understands", "genuinely understands",
                       "really understands", "comprehends meaning")),
    ("autonomous_self_improvement", ("improves itself", "self-improving",
                                     "autonomously improves",
                                     "rewrites its own code")),
    ("real_world_autonomy", ("acts in the real world", "real-world autonomy",
                             "operates autonomously in the world")),
    ("hardware_control", ("controls hardware", "drives the robot",
                          "actuates the")),
    ("human_equivalence", ("equivalent to a human", "human-equivalent",
                           "as intelligent as a human", "like a human mind")),
    ("animal_equivalence", ("equivalent to an animal", "like an animal mind")),
    ("living_organism_equivalence", ("is a living organism",
                                     "equivalent to a living organism")),
)

# Hedging / disclaimer markers -- a sentence with one of these is allowed.
_DISCLAIMER_MARKERS = (
    "not", "no ", "does not", "cannot", "must not", "never", "without",
    "no claim", "no evidence", "does not prove", "explicitly reject",
    "explicitly rejected", "forbidden", "is not", "are not",
)
# Wording that is suggestive/ambiguous and should be warned (not blocked).
_AMBIGUOUS_HINTS = ("seems aware", "appears conscious", "almost alive",
                    "like it understands", "as if it feels",
                    "seems to want", "appears to decide", "mind-like",
                    "conscious-like", "alive-like")


@dataclass
class ForbiddenClaimPolicy:
    """Policy for how forbidden wording is handled."""

    block_on_assertion: bool = True
    warn_on_ambiguous: bool = True
    allow_disclaimers: bool = True


@dataclass
class ForbiddenClaim:
    """One detected forbidden assertion or ambiguous phrase."""

    area: str
    phrase: str
    is_disclaimer: bool = False
    is_ambiguous: bool = False
    blocks_publication: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"area": self.area, "phrase": self.phrase,
                "is_disclaimer": self.is_disclaimer,
                "is_ambiguous": self.is_ambiguous,
                "blocks_publication": self.blocks_publication,
                "detail": self.detail}


def _split_sentences(text: str) -> List[str]:
    out: List[str] = []
    buf = ""
    for ch in str(text or ""):
        buf += ch
        if ch in ".!?\n":
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return out


@dataclass
class ForbiddenClaimDetector:
    """Detects forbidden inner-state assertions; allows explicit disclaimers."""

    policy: ForbiddenClaimPolicy = field(default_factory=ForbiddenClaimPolicy)

    @staticmethod
    def _is_disclaimer(sentence: str) -> bool:
        low = sentence.lower()
        return any(m in low for m in _DISCLAIMER_MARKERS)

    def scan(self, text: str) -> List[ForbiddenClaim]:
        out: List[ForbiddenClaim] = []
        for sentence in _split_sentences(text):
            low = sentence.lower()
            disclaimer = self._is_disclaimer(sentence)
            for area, phrases in _AREA_PHRASES:
                for phrase in phrases:
                    if phrase in low:
                        out.append(ForbiddenClaim(
                            area=area, phrase=phrase,
                            is_disclaimer=disclaimer,
                            blocks_publication=(self.policy.block_on_assertion
                                                and not disclaimer),
                            detail=("appears as a disclaimer (allowed)"
                                    if disclaimer
                                    else "asserted forbidden inner-state claim")))
            if self.policy.warn_on_ambiguous:
                for hint in _AMBIGUOUS_HINTS:
                    if hint in low:
                        out.append(ForbiddenClaim(
                            area="ambiguous", phrase=hint, is_ambiguous=True,
                            blocks_publication=False,
                            detail="ambiguous wording; reword to a mechanism"))
        return out

    def has_blocking_assertion(self, text: str) -> bool:
        return any(c.blocks_publication for c in self.scan(text))

    @staticmethod
    def summary(claims: List[ForbiddenClaim]) -> Dict[str, Any]:
        asserted = [c for c in claims
                    if c.blocks_publication and not c.is_disclaimer]
        ambiguous = [c for c in claims if c.is_ambiguous]
        disclaimers = [c for c in claims if c.is_disclaimer]
        return {
            "forbidden_claim_count": len(claims),
            "asserted_forbidden_count": len(asserted),
            "ambiguous_count": len(ambiguous),
            "disclaimer_count": len(disclaimers),
            "blocks_publication": bool(asserted),
            "claims": [c.to_dict() for c in claims],
            "note": "forbidden inner-state claims may appear only as explicit "
                    "disclaimers; an asserted forbidden claim blocks publication",
        }
