"""Membrane salience modulation -- attention weighting, not truth or intelligence.

:class:`MembraneSalienceModulator` scores how much a sensory impression should stand
out, from novelty, recurrence, absence, rhythm shift, source reliability/diversity,
cross-source co-occurrence, payload change, overload/deprivation, contamination risk,
and operator-pulse/human-text/debug-gloss weights. Salience is not truth and not
intelligence: high salience can still be contaminated, and operator-pulse and
human-text salience are capped by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SalienceFactor:
    NOVELTY = "novelty"
    RECURRENCE = "recurrence"
    ABSENCE = "absence"
    RHYTHM_SHIFT = "rhythm_shift"
    SOURCE_RELIABILITY = "source_reliability"
    SOURCE_DIVERSITY = "source_diversity"
    CROSS_SOURCE = "cross_source_co_occurrence"
    PAYLOAD_CHANGE = "payload_change"
    OVERLOAD = "overload"
    DEPRIVATION = "deprivation"
    CONTAMINATION_RISK = "contamination_risk"
    OPERATOR_WEIGHT = "operator_pulse_weight"
    HUMAN_TEXT_WEIGHT = "human_text_weight"
    DEBUG_GLOSS_WEIGHT = "debug_gloss_weight"

    ALL = (NOVELTY, RECURRENCE, ABSENCE, RHYTHM_SHIFT, SOURCE_RELIABILITY,
           SOURCE_DIVERSITY, CROSS_SOURCE, PAYLOAD_CHANGE, OVERLOAD,
           DEPRIVATION, CONTAMINATION_RISK, OPERATOR_WEIGHT, HUMAN_TEXT_WEIGHT,
           DEBUG_GLOSS_WEIGHT)


@dataclass
class SalienceScore:
    """The salience of one sensory impression (attention weight, not truth)."""

    score: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    capped: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "salience": round(self.score, 3), "capped": self.capped,
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "notes": list(self.notes),
            "note": "salience is attention weighting, not truth or intelligence; "
                    "high salience can still be contaminated; operator-pulse and "
                    "human-text salience are capped by default",
        }


@dataclass
class MembraneSalienceModulator:
    """Modulates per-impression salience with conservative caps."""

    operator_pulse_cap: float = 0.4
    human_text_cap: float = 0.5

    def modulate(self, *, novelty: float = 0.0, recurrence: float = 0.0,
                 is_absence: bool = False, source_reliability: float = 0.7,
                 source_count: int = 1, payload_change: float = 0.0,
                 overload: float = 0.0, deprivation: float = 0.0,
                 contamination: float = 0.0, operator_weight: float = 0.0,
                 human_text_weight: float = 0.0, debug_gloss_weight: float = 0.0,
                 ) -> SalienceScore:
        f: Dict[str, float] = {}
        f[SalienceFactor.NOVELTY] = max(0.0, min(1.0, novelty))
        f[SalienceFactor.RECURRENCE] = max(0.0, min(1.0, recurrence))
        f[SalienceFactor.ABSENCE] = 0.6 if is_absence else 0.2
        f[SalienceFactor.SOURCE_RELIABILITY] = max(0.0, min(
            1.0, source_reliability))
        f[SalienceFactor.SOURCE_DIVERSITY] = 0.8 if source_count >= 2 else 0.4
        f[SalienceFactor.PAYLOAD_CHANGE] = max(0.0, min(1.0, payload_change))
        f[SalienceFactor.OVERLOAD] = max(0.0, min(1.0, overload))
        f[SalienceFactor.DEPRIVATION] = max(0.0, min(1.0, deprivation))
        f[SalienceFactor.CONTAMINATION_RISK] = max(0.0, min(1.0, contamination))

        base = (0.35 * f[SalienceFactor.NOVELTY]
                + 0.15 * f[SalienceFactor.ABSENCE]
                + 0.15 * f[SalienceFactor.SOURCE_RELIABILITY]
                + 0.1 * f[SalienceFactor.SOURCE_DIVERSITY]
                + 0.15 * f[SalienceFactor.PAYLOAD_CHANGE]
                + 0.1 * max(f[SalienceFactor.OVERLOAD],
                            f[SalienceFactor.DEPRIVATION]))
        score = SalienceScore(score=base, factors=f)

        # Contamination lowers usable salience (but is still recorded).
        if contamination >= 0.5:
            score.notes.append("high contamination lowers usable salience")
            score.score *= 0.5
        # Operator-pulse / human-text caps.
        if operator_weight >= 0.5:
            score.score = min(score.score, self.operator_pulse_cap)
            score.capped = True
            score.notes.append("operator-pulse salience capped")
        if human_text_weight >= 0.5:
            score.score = min(score.score, self.human_text_cap)
            score.capped = True
            score.notes.append("human-text salience capped")
        score.score = round(max(0.0, min(1.0, score.score)), 4)
        return score
