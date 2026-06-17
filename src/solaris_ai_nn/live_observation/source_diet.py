"""Live source diet -- the balance of the live field, read-only.

:class:`LiveSourceDietAnalyzer` measures the proportion of events by source and
modality, dominance concentration, over/under-represented sources, human-text and
operator-pulse dominance, and scalar/absence balance. No source should silently
dominate, the operator pulse should not dominate the first-birth field, and human
text must not become the primary ontology. Recommendations are report-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")
_DOMINANCE_THRESHOLD = 0.6
_OPERATOR_PULSE_THRESHOLD = 0.4
_HUMAN_TEXT_THRESHOLD = 0.5


class SourceDietBalance:
    BALANCED = "balanced"
    MILD_DOMINANCE = "mild_dominance"
    OPERATOR_PULSE_DOMINANT = "operator_pulse_dominant"
    HUMAN_TEXT_DOMINANT = "human_text_dominant"
    SINGLE_SOURCE = "single_source"
    EMPTY = "empty"

    ALL = (BALANCED, MILD_DOMINANCE, OPERATOR_PULSE_DOMINANT,
           HUMAN_TEXT_DOMINANT, SINGLE_SOURCE, EMPTY)


@dataclass
class SourceDietFinding:
    """One source-diet finding (report-only)."""

    finding: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding": self.finding, "detail": self.detail}


@dataclass
class LiveSourceDiet:
    """The computed source diet over accepted events."""

    total_events: int = 0
    by_source: Dict[str, float] = field(default_factory=dict)
    by_modality: Dict[str, float] = field(default_factory=dict)
    dominance_score: float = 0.0
    operator_pulse_proportion: float = 0.0
    human_text_proportion: float = 0.0
    dominant_source: str = ""
    balance: str = SourceDietBalance.EMPTY
    findings: List[SourceDietFinding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_events,
            "by_source": {k: round(v, 3) for k, v in self.by_source.items()},
            "by_modality": {k: round(v, 3)
                            for k, v in self.by_modality.items()},
            "live_source_diet_dominance_score": round(self.dominance_score, 3),
            "live_operator_pulse_dominance_score": round(
                self.operator_pulse_proportion, 3),
            "human_text_proportion": round(self.human_text_proportion, 3),
            "dominant_source": self.dominant_source,
            "balance": self.balance,
            "findings": [f.to_dict() for f in self.findings],
            "note": "no source should silently dominate; operator pulse should "
                    "not dominate the first-birth field; human text must not "
                    "become the primary ontology; recommendations are report-only",
        }


@dataclass
class LiveSourceDietAnalyzer:
    """Computes the source diet balance from accepted events."""

    def analyze(self, accepted_events: List[Dict[str, Any]]) -> LiveSourceDiet:
        diet = LiveSourceDiet(total_events=len(accepted_events))
        if not accepted_events:
            diet.findings.append(SourceDietFinding(
                "empty", "no accepted events to assess source diet"))
            return diet
        src_counts: Dict[str, int] = {}
        mod_counts: Dict[str, int] = {}
        human_text = 0
        for ev in accepted_events:
            sid = ev.get("source_id", "")
            src_counts[sid] = src_counts.get(sid, 0) + 1
            mod = ev.get("modality", "")
            mod_counts[mod] = mod_counts.get(mod, 0) + 1
            if sid in _HUMAN_TEXT_SOURCES:
                human_text += 1
        n = len(accepted_events)
        diet.by_source = {k: v / n for k, v in src_counts.items()}
        diet.by_modality = {k: v / n for k, v in mod_counts.items()}
        diet.dominant_source = max(src_counts, key=src_counts.get)
        diet.dominance_score = max(diet.by_source.values())
        diet.operator_pulse_proportion = diet.by_source.get(_OPERATOR_PULSE, 0.0)
        diet.human_text_proportion = human_text / n

        if len(src_counts) == 1:
            diet.balance = SourceDietBalance.SINGLE_SOURCE
            diet.findings.append(SourceDietFinding(
                "single_source", f"all events from {diet.dominant_source!r}"))
        elif diet.operator_pulse_proportion >= _OPERATOR_PULSE_THRESHOLD:
            diet.balance = SourceDietBalance.OPERATOR_PULSE_DOMINANT
            diet.findings.append(SourceDietFinding(
                "operator_pulse_dominant",
                "operator pulse dominates the live field; it should be stimulus, "
                "not the primary source"))
        elif diet.human_text_proportion >= _HUMAN_TEXT_THRESHOLD:
            diet.balance = SourceDietBalance.HUMAN_TEXT_DOMINANT
            diet.findings.append(SourceDietFinding(
                "human_text_dominant",
                "human text dominates; it must not become the primary ontology"))
        elif diet.dominance_score >= _DOMINANCE_THRESHOLD:
            diet.balance = SourceDietBalance.MILD_DOMINANCE
            diet.findings.append(SourceDietFinding(
                "mild_dominance",
                f"{diet.dominant_source!r} accounts for "
                f"{diet.dominance_score:.0%} of events"))
        else:
            diet.balance = SourceDietBalance.BALANCED
        return diet

    @property
    def operator_text_dominant(self) -> bool:  # pragma: no cover - helper
        return False
