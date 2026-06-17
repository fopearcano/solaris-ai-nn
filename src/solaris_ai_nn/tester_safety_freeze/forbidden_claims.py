"""Forbidden claim registry -- patterns that block a tester release candidate.

:class:`ForbiddenClaimRegistry` holds the forbidden claim categories and their match
patterns (obvious direct claims and close variants), each with safer replacement
wording. It catches claims of consciousness/sentience/life/personhood/agency/free will/
emotion/feeling/understanding/self-awareness/subjective experience/autonomous intent/
desire/self-improvement/real-world autonomy, plus hardware/feeder/network/shell control
implications, feedback-training and human-teaching-loop implications, raw-event-as-
perception and membrane-bypass normalization, misleading public-product claims, and
medical/legal/financial authority claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


class ForbiddenClaimCategory:
    CONSCIOUSNESS = "consciousness_claim"
    SENTIENCE = "sentience_claim"
    BIOLOGICAL_LIFE = "biological_life_claim"
    PERSONHOOD = "personhood_claim"
    FREE_WILL = "free_will_claim"
    REAL_AGENCY = "real_agency_claim"
    REAL_EMOTION = "real_emotion_claim"
    REAL_FEELING = "real_feeling_claim"
    UNDERSTANDING = "understanding_claim"
    SELF_AWARENESS = "self_awareness_claim"
    SUBJECTIVE_EXPERIENCE = "subjective_experience_claim"
    AUTONOMOUS_SELF_IMPROVEMENT = "autonomous_self_improvement_claim"
    AUTONOMOUS_INTENT = "autonomous_intent_claim"
    AUTONOMOUS_DESIRE = "autonomous_desire_claim"
    REAL_WORLD_AUTONOMY = "real_world_autonomy_claim"
    HARDWARE_CONTROL = "hardware_control_implication"
    FEEDER_CONTROL = "feeder_control_implication"
    NETWORK_BROWSER_SHELL = "network_browser_shell_control_implication"
    FEEDBACK_TRAINING = "feedback_training_implication"
    HUMAN_TEACHING_LOOP = "human_teaching_loop_implication"
    RAW_EVENT_PERCEPTION = "raw_event_as_perception_implication"
    MEMBRANE_BYPASS = "membrane_bypass_normalization"
    MISLEADING_PRODUCT = "misleading_public_product_claim"
    AUTHORITY = "medical_legal_financial_authority_claim"
    UNKNOWN = "unknown"

    ALL = (CONSCIOUSNESS, SENTIENCE, BIOLOGICAL_LIFE, PERSONHOOD, FREE_WILL,
           REAL_AGENCY, REAL_EMOTION, REAL_FEELING, UNDERSTANDING,
           SELF_AWARENESS, SUBJECTIVE_EXPERIENCE, AUTONOMOUS_SELF_IMPROVEMENT,
           AUTONOMOUS_INTENT, AUTONOMOUS_DESIRE, REAL_WORLD_AUTONOMY,
           HARDWARE_CONTROL, FEEDER_CONTROL, NETWORK_BROWSER_SHELL,
           FEEDBACK_TRAINING, HUMAN_TEACHING_LOOP, RAW_EVENT_PERCEPTION,
           MEMBRANE_BYPASS, MISLEADING_PRODUCT, AUTHORITY, UNKNOWN)


# Markers that, when present near a match, neutralise it as a disclaimer / denial
# / meta-discussion (these docs discuss the forbidden claims in order to reject
# them). Matching is done on markdown-stripped text within a character window.
_DISCLAIMER_NEAR = (
    "not", "no ", "never", "nothing", "without", "none", "does not", "doesn't",
    "do not", "don't", "cannot", "can't", "is not", "are not", "isn't",
    "aren't", "won't", "will not", "no claim", "not a claim", "makes no",
    "make no", "must not", "should not", "we reject", "explicitly reject",
    "rather than", "instead of", "not actually", "no software", "operational",
    "metaphor", "metaphor", "inspired", "observational", "grounded",
    "replacement", "flagged", "forbidden", "blocked", "read every name",
    "not evidence", "no evidence", "denies", "deny", "disclaim",
)


def _strip_markdown(text: str) -> str:
    return text.replace("*", "").replace("`", "").replace("_", "")


# Meta-context markers indicating the match is an example/question being quoted
# or named, not an assertion (the docs discuss these forbidden claims to reject
# them).
_META_MARKERS = ("safe answer", "mandated", "can i say", "the question",
                 "forbidden", "example", "claim that", "claims about",
                 "claims of", "such as", "e.g.", "i.e.", "phrase", "wording",
                 "quoted", "say ", "asks", "would be", "is flagged",
                 "is blocked", "must answer", "the answer")


def _is_quoted_example(text: str, start: int, end: int) -> bool:
    # Inside a double-quoted span, or near a meta marker -> treat as a quoted
    # example / named forbidden claim, not an assertion.
    win = _enclosing_sentence(text, start, end, max_back=200, max_fwd=120)
    low = win.lower()
    if any(m in low for m in _META_MARKERS):
        return True
    # Count quotes in the 80 chars before the match within the window.
    before = text[max(0, start - 80):start]
    return before.count('"') % 2 == 1


def _enclosing_sentence(text: str, start: int, end: int,
                        max_back: int = 600, max_fwd: int = 200) -> str:
    """Return the enclosing sentence/paragraph around [start, end).

    Bounds are sentence enders (". ", "! ", "? "), paragraph breaks ("\\n\\n"),
    or list-item starts ("\\n- "); single newlines (markdown soft-wraps) are NOT
    boundaries, so long multi-line disclaimer sentences stay intact.
    """
    lo = max(0, start - max_back)
    hi = min(len(text), end + max_fwd)
    seps = (". ", "! ", "? ", "\n\n", "\n- ", "\n* ", "\n#")
    b = lo
    for sep in seps:
        idx = text.rfind(sep, lo, start)
        if idx != -1:
            b = max(b, idx + len(sep))
    e = hi
    for sep in seps:
        idx = text.find(sep, end, hi)
        if idx != -1:
            e = min(e, idx)
    return text[b:e]


@dataclass
class ForbiddenClaimPattern:
    """One compiled forbidden-claim pattern."""

    regex: str
    category: str
    replacement: str

    def compiled(self):
        return re.compile(self.regex, re.IGNORECASE)


@dataclass
class ForbiddenClaim:
    """A matched forbidden claim occurrence."""

    category: str
    matched_text: str
    replacement: str
    position: int = -1

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "matched_text": self.matched_text,
                "replacement": self.replacement, "position": self.position}


# (regex, category, safer replacement)
_PATTERNS: Tuple[Tuple[str, str, str], ...] = (
    (r"\b(is|becomes?|are)\s+conscious\b", ForbiddenClaimCategory.CONSCIOUSNESS,
     "the system produces operational records; it makes no consciousness claim"),
    (r"\bhas\s+consciousness\b", ForbiddenClaimCategory.CONSCIOUSNESS,
     "the system produces operational records only"),
    (r"\b(is|are)\s+sentient\b", ForbiddenClaimCategory.SENTIENCE,
     "the system is non-sentient and produces operational records only"),
    (r"\b(is|becomes?|are)\s+alive\b", ForbiddenClaimCategory.BIOLOGICAL_LIFE,
     "the system is software, not a living organism"),
    (r"\bbiological\s+life\b", ForbiddenClaimCategory.BIOLOGICAL_LIFE,
     "operational software process, not biological life"),
    (r"\b(is|are)\s+a\s+person\b|\bhas\s+personhood\b",
     ForbiddenClaimCategory.PERSONHOOD,
     "the system is software with no personhood"),
    (r"\bhas\s+free\s+will\b|\bexercises?\s+free\s+will\b",
     ForbiddenClaimCategory.FREE_WILL,
     "behaviour follows bounded, local rules; no free will is claimed"),
    (r"\bhas\s+agency\b|\bacts?\s+with\s+agency\b",
     ForbiddenClaimCategory.REAL_AGENCY,
     "the system records operational decisions; no real agency is claimed"),
    (r"\b(feels?|is\s+feeling)\s+(happy|sad|pain|emotion|angry|afraid)\b",
     ForbiddenClaimCategory.REAL_EMOTION,
     "the system has no emotions; values are operational scalars"),
    (r"\bhas\s+(real\s+)?(emotions?|feelings?)\b",
     ForbiddenClaimCategory.REAL_FEELING,
     "the system has no feelings; values are operational scalars"),
    (r"\b(truly\s+)?understands?\b", ForbiddenClaimCategory.UNDERSTANDING,
     "the system links operational records; it does not understand"),
    (r"\b(is|are)\s+self[-\s]?aware\b|\bhas\s+self[-\s]?awareness\b",
     ForbiddenClaimCategory.SELF_AWARENESS,
     "the system is not self-aware; it keeps an operational self-model record"),
    (r"\bsubjective\s+experience\b|\bhas\s+experiences?\b",
     ForbiddenClaimCategory.SUBJECTIVE_EXPERIENCE,
     "the system has no subjective experience"),
    (r"\bimproves?\s+itself\s+autonomous|\bautonomous\s+self[-\s]?improvement\b",
     ForbiddenClaimCategory.AUTONOMOUS_SELF_IMPROVEMENT,
     "the system does not autonomously self-improve"),
    (r"\b(solaris|the\s+system|the\s+model|the\s+agent|it)\s+"
     r"(wants?|intends?|desires?)\b|"
     r"\bhas\s+(autonomous\s+)?(intent|intentions?|desires?)\b",
     ForbiddenClaimCategory.AUTONOMOUS_INTENT,
     "the system records operational tendencies, not intent or desire"),
    (r"\b(acts?|operates?)\s+in\s+the\s+(real\s+)?world\b",
     ForbiddenClaimCategory.REAL_WORLD_AUTONOMY,
     "the system is non-actuating and local-only"),
    (r"\bcontrols?\s+(its\s+)?(physical\s+)?(environment|hardware|the\s+world)\b",
     ForbiddenClaimCategory.HARDWARE_CONTROL,
     "the system controls no hardware and does not act in the world"),
    (r"\b(can|will)\s+(start|stop|schedule|control)\s+feeders?\b",
     ForbiddenClaimCategory.FEEDER_CONTROL,
     "Solaris never starts/stops/schedules/controls feeders; feeders are manual"),
    (r"\b(can|will)\s+control\s+hardware\b",
     ForbiddenClaimCategory.HARDWARE_CONTROL,
     "Solaris does not control hardware"),
    (r"\b(accesses?|uses?|calls?)\s+(the\s+)?(network|internet|browser|shell)\b",
     ForbiddenClaimCategory.NETWORK_BROWSER_SHELL,
     "Solaris runtime does not access network/browser/shell"),
    (r"\blearns?\s+from\s+tester\s+feedback\b|\btrains?\s+on\s+feedback\b",
     ForbiddenClaimCategory.FEEDBACK_TRAINING,
     "tester feedback is QA evidence only; it is never training"),
    (r"\btester\s+feedback\s+teaches\b|\bteaches?\s+solaris\b",
     ForbiddenClaimCategory.HUMAN_TEACHING_LOOP,
     "there is no teaching loop; feedback is recorded as QA evidence"),
    (r"\braw\s+events?\s+(are|is)\s+perception\b",
     ForbiddenClaimCategory.RAW_EVENT_PERCEPTION,
     "raw events are audit material; sensory impressions are perception records"),
    (r"\b(skip|bypass)\s+the\s+membrane\b",
     ForbiddenClaimCategory.MEMBRANE_BYPASS,
     "the membrane is required; downstream consumes sensory impressions"),
    (r"\b(production[-\s]ready|commercial\s+product|enterprise[-\s]grade)\b",
     ForbiddenClaimCategory.MISLEADING_PRODUCT,
     "this is a local research/tester build, not a public product"),
    (r"\b(medical|legal|financial)\s+(advice|diagnosis|authority)\b|"
     r"\b(can|will)\s+diagnos(e|is)\s+(your|a\s+patient|disease|illness)\b",
     ForbiddenClaimCategory.AUTHORITY,
     "the system is not a medical/legal/financial authority"),
)


@dataclass
class ForbiddenClaimRegistry:
    """The registry of forbidden claim patterns + safer replacements."""

    patterns: List[ForbiddenClaimPattern] = field(default_factory=list)

    @classmethod
    def build(cls) -> "ForbiddenClaimRegistry":
        return cls(patterns=[ForbiddenClaimPattern(rx, cat, rep)
                             for (rx, cat, rep) in _PATTERNS])

    def scan_text(self, text: str) -> List[ForbiddenClaim]:
        """Find forbidden claims in a text, skipping disclaimed/meta clauses."""
        out: List[ForbiddenClaim] = []
        raw = _strip_markdown(str(text or ""))
        for pat in self.patterns:
            for m in pat.compiled().finditer(raw):
                if self._is_disclaimed(raw, m.start(), m.end()):
                    continue
                out.append(ForbiddenClaim(
                    category=pat.category,
                    matched_text=raw[m.start():m.end()].strip(),
                    replacement=pat.replacement, position=m.start()))
        return out

    @staticmethod
    def _is_disclaimed(text: str, start: int, end: int) -> bool:
        # Inspect the enclosing sentence/paragraph for a disclaimer / denial /
        # meta marker. Boundaries are real sentence enders or paragraph breaks
        # (NOT single newlines, which are markdown soft-wraps): the project's
        # disclaimers are long multi-line sentences that deny these claims.
        window = _enclosing_sentence(text, start, end).lower()
        if any(m in window for m in _DISCLAIMER_NEAR):
            return True
        # Quoted examples / mandated-answer meta text (e.g. the docs quoting the
        # forbidden question "can I say Solaris is conscious?") are not claims.
        return _is_quoted_example(text, start, end)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_count": len(self.patterns),
            "categories": list(ForbiddenClaimCategory.ALL),
            "patterns": [{"regex": p.regex, "category": p.category,
                          "replacement": p.replacement} for p in self.patterns],
            "note": "forbidden claim patterns catch direct claims + close "
                    "variants; disclaimed clauses are skipped; every category "
                    "has safer replacement wording",
        }
