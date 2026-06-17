"""Live recurrence tracker -- recurrence requires multiple observations.

:class:`LiveRecurrenceTracker` groups feature vectors by signature and records
recurring payload shapes, scalar ranges, source co-occurrences, absence windows,
rhythm-linked patterns, and operator-pulse patterns. Recurrence requires multiple
observations: a single event cannot birth a concept, operator-pulse recurrence alone
cannot birth a core environmental concept, and human-text recurrence is marked a
contamination risk unless it is feature-grounded elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .feature_extraction import LiveFeatureVector

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")


class RecurrenceStrength:
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    UNSTABLE = "unstable"
    INCONCLUSIVE = "inconclusive"

    ALL = (NONE, WEAK, MODERATE, STRONG, UNSTABLE, INCONCLUSIVE)


@dataclass
class RecurrencePattern:
    """One recurring feature signature and its observed support."""

    feature_signature: str
    count: int = 0
    source_distribution: Dict[str, int] = field(default_factory=dict)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    absence_count: int = 0
    noisy_count: int = 0
    rhythm_markers: List[str] = field(default_factory=list)
    event_ids: List[str] = field(default_factory=list)
    strength: str = RecurrenceStrength.NONE
    contamination_risk: List[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.source_distribution)

    @property
    def operator_only(self) -> bool:
        return set(self.source_distribution) == {_OPERATOR_PULSE} \
            and bool(self.source_distribution)

    @property
    def human_text_only(self) -> bool:
        return bool(self.source_distribution) and all(
            s in _HUMAN_TEXT_SOURCES for s in self.source_distribution)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_signature": self.feature_signature, "count": self.count,
            "source_distribution": dict(self.source_distribution),
            "modality_distribution": dict(self.modality_distribution),
            "source_count": self.source_count,
            "absence_count": self.absence_count, "noisy_count": self.noisy_count,
            "rhythm_markers": list(dict.fromkeys(self.rhythm_markers)),
            "strength": self.strength,
            "operator_only": self.operator_only,
            "human_text_only": self.human_text_only,
            "contamination_risk": list(self.contamination_risk),
            "event_ids": self.event_ids[:50],
        }


@dataclass
class LiveRecurrenceTracker:
    """Tracks recurring feature signatures from feature vectors."""

    min_recurrence: int = 3

    def track(self, vectors: List[LiveFeatureVector]) -> List[RecurrencePattern]:
        patterns: Dict[str, RecurrencePattern] = {}
        for v in vectors:
            sig = v.feature_signature
            p = patterns.get(sig)
            if p is None:
                p = RecurrencePattern(feature_signature=sig)
                patterns[sig] = p
            p.count += 1
            p.source_distribution[v.source_id] = \
                p.source_distribution.get(v.source_id, 0) + 1
            p.modality_distribution[v.modality] = \
                p.modality_distribution.get(v.modality, 0) + 1
            if v.is_absence:
                p.absence_count += 1
            if v.is_noisy:
                p.noisy_count += 1
            if v.rhythm_marker:
                p.rhythm_markers.append(v.rhythm_marker)
            p.event_ids.append(v.event_id)
        for p in patterns.values():
            self._finalize(p)
        return list(patterns.values())

    def _finalize(self, p: RecurrencePattern) -> None:
        # Strength from count + source diversity (recurrence needs >1 event).
        if p.count <= 1:
            p.strength = RecurrenceStrength.NONE
        elif p.count < self.min_recurrence:
            p.strength = RecurrenceStrength.WEAK
        elif p.noisy_count >= max(2, p.count - 1):
            p.strength = RecurrenceStrength.UNSTABLE
        elif p.source_count >= 2 and p.count >= self.min_recurrence + 2:
            p.strength = RecurrenceStrength.STRONG
        else:
            p.strength = RecurrenceStrength.MODERATE

        # Contamination risk markers (recorded, never hidden).
        if p.operator_only:
            p.contamination_risk.append(
                "operator-pulse recurrence alone cannot birth a core "
                "environmental concept")
        if p.human_text_only:
            p.contamination_risk.append(
                "human-text recurrence is a contamination risk unless "
                "feature-grounded by another source")

    @staticmethod
    def summary(patterns: List[RecurrencePattern]) -> Dict[str, Any]:
        def count(strength):
            return sum(1 for p in patterns if p.strength == strength)
        return {
            "live_recurrence_pattern_count": len(patterns),
            "strong_pattern_count": count(RecurrenceStrength.STRONG),
            "moderate_pattern_count": count(RecurrenceStrength.MODERATE),
            "weak_pattern_count": count(RecurrenceStrength.WEAK),
            "unstable_pattern_count": count(RecurrenceStrength.UNSTABLE),
            "patterns": [p.to_dict() for p in patterns],
            "note": "recurrence requires multiple observations; a single event "
                    "cannot birth a concept; operator-pulse-only recurrence is "
                    "insufficient; human-text-only recurrence is a contamination "
                    "risk",
        }
