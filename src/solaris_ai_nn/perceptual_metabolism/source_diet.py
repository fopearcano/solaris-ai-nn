"""Source diet -- what mix of sources the organism has been consuming.

A :class:`SourceDietAnalyzer` measures the perceptual diet across modality classes
(human-like / non-human / machine-native / absence), human-labelled vs
feature-only streams, and live vs fixture/replay streams. Human-like, non-human,
and mixed diets are all allowed; dominance must be *measured*, not hidden, and
human-label dominance is reported explicitly. The diet shapes the kind of
internal structure that emerges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..plural_sensorium.modality import ModalityClass, modality_class_for


@dataclass
class SourceDietProfile:
    modality_event_counts: Dict[str, int] = field(default_factory=dict)
    class_event_counts: Dict[str, int] = field(default_factory=dict)
    human_labelled_events: int = 0
    feature_only_events: int = 0
    live_events: int = 0
    fixture_events: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SourceDietBalance:
    diet_diversity: float
    modality_dominance: float
    human_label_dominance: float
    non_human_contribution: float
    silence_contribution: float
    cross_modal_contribution: float
    source_reliability_balance: float
    live_vs_fixture_balance: float
    dominant_modality: str = ""
    dominant_class: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: (round(v, 4) if isinstance(v, float) else v)
                   for k, v in self.__dict__.items()},
                "note": "human-like / non-human / mixed diets are all allowed; "
                        "dominance is measured, never hidden"}


@dataclass
class SourceDietAnalyzer:
    """Computes the perceptual diet profile and balance from sensorium state."""

    def analyze(self, sensorium: Any, *,
                source_health: Any = None) -> SourceDietBalance:
        profile = SourceDietProfile()
        receptors = list(getattr(sensorium, "receptors", {}).values())
        total = 0
        for r in receptors:
            n = getattr(r, "event_count", 0)
            if n <= 0:
                continue
            modality = getattr(r, "modality", "unknown_field")
            profile.modality_event_counts[modality] = \
                profile.modality_event_counts.get(modality, 0) + n
            klass = modality_class_for(modality)
            profile.class_event_counts[klass] = \
                profile.class_event_counts.get(klass, 0) + n
            total += n
            if getattr(r, "reliability", 1.0) < 0.8:
                pass  # reflected in reliability balance below

        total = max(1, total)
        # Diet diversity: normalized entropy over modalities.
        diversity = self._entropy(list(
            profile.modality_event_counts.values()))
        dominance = (max(profile.modality_event_counts.values()) / total
                     if profile.modality_event_counts else 0.0)
        dominant_modality = (max(profile.modality_event_counts,
                                 key=profile.modality_event_counts.get)
                             if profile.modality_event_counts else "")
        dominant_class = (max(profile.class_event_counts,
                              key=profile.class_event_counts.get)
                          if profile.class_event_counts else "")

        human_class = profile.class_event_counts.get(
            ModalityClass.HUMAN_LIKE, 0)
        non_human = (profile.class_event_counts.get(ModalityClass.NON_HUMAN, 0)
                     + profile.class_event_counts.get(
                         ModalityClass.MACHINE_NATIVE, 0))
        absence = profile.class_event_counts.get(ModalityClass.ABSENCE_BASED, 0)

        contamination = (sensorium.human_label_contamination_score()
                         if hasattr(sensorium, "human_label_contamination_score")
                         else 0.0)
        reliability = (sum(getattr(r, "reliability", 1.0) for r in receptors)
                       / max(1, len(receptors)))

        live = fixture = 0
        if source_health is not None:
            live = len(getattr(source_health, "active_sources", lambda: [])())
        cross_modal = (sensorium.cross_modal.relation_count()
                       if hasattr(sensorium, "cross_modal") else 0)

        return SourceDietBalance(
            diet_diversity=diversity,
            modality_dominance=dominance,
            human_label_dominance=max(human_class / total, contamination),
            non_human_contribution=non_human / total,
            silence_contribution=absence / total,
            cross_modal_contribution=min(1.0, cross_modal / total),
            source_reliability_balance=reliability,
            live_vs_fixture_balance=(live / (live + max(1, len(receptors)))
                                     if (live or receptors) else 0.0),
            dominant_modality=dominant_modality,
            dominant_class=dominant_class)

    @staticmethod
    def _entropy(counts: List[int]) -> float:
        import math

        total = sum(counts)
        if total <= 0 or len(counts) <= 1:
            return 0.0
        probs = [c / total for c in counts if c > 0]
        ent = -sum(p * math.log(p, 2) for p in probs)
        max_ent = math.log(len(probs), 2) if len(probs) > 1 else 1.0
        return round(ent / max_ent, 4) if max_ent else 0.0
