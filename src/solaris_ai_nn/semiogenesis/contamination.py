"""Sign contamination -- making human-language domination visible, not forbidden.

The :class:`SignContaminationAnalyzer` detects when a sign is driven by human
language rather than perceptual structure (a human word used as a sign code, a
gloss replacing the sign, a human label treated as ground, a text stream
dominating sign formation). Human-readable gloss is allowed; human-language
domination is measured, and contaminated signs remain useful but are marked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .signs import InternalSign, SignGrounding, SignKind
from .translation_gloss import GlossStatus

# A short list of common human words; a sign_code that is a plain human word is a
# contamination signal (operational codes look like ``rf:03a``, not ``dog``).
_COMMON_WORDS = {
    "dog", "cat", "person", "room", "house", "sentence", "word", "object",
    "thing", "car", "tree", "door", "voice", "speech", "music", "animal",
}


@dataclass
class SignContaminationReport:
    sign_id: str
    contamination_score: float
    flags: List[str] = field(default_factory=list)
    feature_grounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "contamination_score": round(self.contamination_score, 4),
            "flags": list(self.flags),
            "feature_grounded": self.feature_grounded,
            "note": "human gloss is allowed but measured; gloss/label is never "
                    "ground truth",
        }


@dataclass
class SignContaminationAnalyzer:
    """Detects and scores human-language contamination of sign formation."""

    def analyze(self, sign: InternalSign) -> SignContaminationReport:
        flags: List[str] = []
        score = 1.0 if sign.kind == SignKind.HUMAN_LABEL_CONTAMINATED else 0.0
        if sign.contamination_flags:
            score = max(score, 0.6)

        code = (sign.sign_code or "").lower()
        # A sign code that is a bare human word (no operational ``prefix:suffix``).
        bare = re.sub(r"[^a-z]", "", code)
        if ":" not in code and bare in _COMMON_WORDS:
            flags.append("human_word_used_as_sign_code")
            score = max(score, 0.8)

        if sign.grounding == SignGrounding.LABEL_GROUNDED:
            flags.append("human_label_treated_as_concept_ground")
            score = max(score, 0.6)

        # Gloss replacing the sign: a gloss present while grounding is near-zero.
        if sign.human_gloss and sign.grounding_score < 0.1:
            flags.append("gloss_replacing_sign")
            score = max(score, 0.5)
        if sign.human_gloss_status == GlossStatus.HUMAN_LABEL_CONTAMINATED:
            flags.append("contaminated_gloss_attached")
            score = max(score, 0.6)

        # A human-text modality dominating the evidence.
        human_text = sign.modality_distribution.get("human_textual", 0)
        total = sum(sign.modality_distribution.values()) or 1
        if human_text / total >= 0.6:
            flags.append("text_stream_dominates_sign_formation")
            score = max(score, human_text / total)

        if score >= 0.5 and SignKind.HUMAN_LABEL_CONTAMINATED not in flags:
            flags.append("annotation_dominates_feature_evidence")

        feature_grounded = score < 0.5
        # Mark (never forbid); lower grounding but keep the sign usable.
        if score >= 0.5:
            sign.grounding_score = round(sign.grounding_score * (1.0 - 0.5
                                                                 * score), 4)
            if "human_label_external" not in sign.contamination_flags:
                sign.contamination_flags.append("human_label_external")
        return SignContaminationReport(
            sign_id=sign.sign_id, contamination_score=round(score, 4),
            flags=flags, feature_grounded=feature_grounded)

    def analyze_all(self, signs: List[InternalSign],
                    ) -> List[SignContaminationReport]:
        return [self.analyze(s) for s in signs]

    @staticmethod
    def contaminated_ratio(reports: List[SignContaminationReport]) -> float:
        if not reports:
            return 0.0
        n = sum(1 for r in reports if not r.feature_grounded)
        return round(n / len(reports), 4)
