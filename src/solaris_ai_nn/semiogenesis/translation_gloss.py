"""Translation gloss -- optional, approximate, debug-only human-readable text.

A :class:`TranslationGloss` provides an optional human-readable explanation of a
sign for reports/debugging. It is never ground truth, never the internal language,
and (for modality-native signs) always marked approximate. Contaminated signs are
marked, and alien signs are never over-translated into human object categories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .signs import InternalSign, SignKind


class GlossStatus:
    NOT_AVAILABLE = "not_available"
    DEBUG_ONLY = "debug_only"
    APPROXIMATE = "approximate"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated"
    OPERATOR_ANNOTATION = "operator_annotation"
    UNSAFE_TO_TRANSLATE = "unsafe_to_translate"

    ALL = (NOT_AVAILABLE, DEBUG_ONLY, APPROXIMATE, HUMAN_LABEL_CONTAMINATED,
           OPERATOR_ANNOTATION, UNSAFE_TO_TRANSLATE)


# Neutral structural descriptors per sign kind (NOT human object categories).
_KIND_DESCRIPTOR = {
    SignKind.MODALITY_NATIVE: "a recurring modality-native structure",
    SignKind.CROSS_MODAL: "a cross-modal relation structure",
    SignKind.ABSENCE: "a recurring absence/silence structure",
    SignKind.RHYTHM: "a recurring rhythm structure",
    SignKind.SOURCE: "a source-behaviour structure",
    SignKind.BOUNDARY: "a boundary/edge structure",
    SignKind.INTERFERENCE: "an interference structure",
    SignKind.METABOLIC: "a metabolic-state structure",
    SignKind.ATTENTION: "an attention-shift structure",
    SignKind.LOGOS_TENSION: "an unresolved-tension marker",
    SignKind.HYPOTHESIS: "a hypothesis reference",
    SignKind.HUMAN_LABEL_CONTAMINATED: "a human-label-influenced structure",
    SignKind.UNKNOWN: "an unclassified structure",
}


@dataclass
class TranslationGloss:
    sign_id: str
    sign_code: str
    text: str
    status: str = GlossStatus.APPROXIMATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "sign_code": self.sign_code,
            "text": self.text,
            "status": self.status,
            "note": "approximate debug gloss only; not ground truth and not the "
                    "internal sign",
        }


@dataclass
class GlossBuilder:
    """Builds approximate, clearly-marked human-readable glosses for signs."""

    def build(self, sign: InternalSign) -> TranslationGloss:
        descriptor = _KIND_DESCRIPTOR.get(sign.kind, "an internal structure")
        modality = sign.dominant_modality or "unknown-modality"
        if sign.is_contaminated:
            status = GlossStatus.HUMAN_LABEL_CONTAMINATED
            text = (f"~{descriptor} over {modality} (human-label contaminated; "
                    "gloss is not reliable and not ground truth)")
        elif sign.kind == SignKind.HUMAN_LABEL_CONTAMINATED:
            status = GlossStatus.HUMAN_LABEL_CONTAMINATED
            text = f"~human-label-influenced structure ({sign.sign_code})"
        else:
            # Modality-native signs are always approximate -- never a human word.
            status = GlossStatus.APPROXIMATE
            text = f"~approx: {descriptor} over {modality} ({sign.sign_code})"
        # Attach to the sign (debug/report only; never ground truth).
        sign.attach_gloss(text, status)
        return TranslationGloss(sign_id=sign.sign_id, sign_code=sign.sign_code,
                                text=text, status=status)

    @staticmethod
    def dependence_score(signs) -> float:
        """Fraction of signs that lean on a human gloss (gloss-dependence)."""
        signs = list(signs)
        if not signs:
            return 0.0
        depended = sum(1 for s in signs
                       if s.human_gloss_status in (
                           GlossStatus.HUMAN_LABEL_CONTAMINATED,
                           GlossStatus.OPERATOR_ANNOTATION))
        return round(depended / len(signs), 4)
