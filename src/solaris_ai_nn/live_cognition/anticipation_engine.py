"""Live anticipation engine -- internal prediction metadata only.

:class:`LiveAnticipationEngine` derives bounded anticipations from eligible private
signs and their concept/source structure: the next source likely active, continued
silence, rhythm continuation, expected recurrence, overload/deprivation risk,
source-health change, co-occurrence, contrast, or explicit uncertainty. Anticipation
is internal prediction metadata only -- it requests no data, controls no feeders, and
acts in no world. Anticipation from operator text alone is blocked / marked
contaminated, and every anticipation carries an uncertainty estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AnticipationType:
    NEXT_SOURCE_ACTIVE = "next_source_likely_active"
    SOURCE_SILENCE_CONTINUES = "source_silence_likely_continues"
    RHYTHM_CONTINUATION = "rhythm_continuation"
    RECURRENCE_EXPECTED = "recurrence_expected"
    OVERLOAD_RISK = "overload_risk_expected"
    DEPRIVATION_RISK = "deprivation_risk_expected"
    SOURCE_HEALTH_CHANGE = "source_health_change_expected"
    CO_OCCURRENCE = "co_occurrence_expected"
    CONTRAST = "contrast_expected"
    UNCERTAINTY = "uncertainty_expected"
    UNKNOWN = "unknown"

    ALL = (NEXT_SOURCE_ACTIVE, SOURCE_SILENCE_CONTINUES, RHYTHM_CONTINUATION,
           RECURRENCE_EXPECTED, OVERLOAD_RISK, DEPRIVATION_RISK,
           SOURCE_HEALTH_CHANGE, CO_OCCURRENCE, CONTRAST, UNCERTAINTY, UNKNOWN)


class AnticipationStatus:
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    CONTAMINATED = "contaminated"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (PROPOSED, SUPPORTED, CONTRADICTED, INCONCLUSIVE, CONTAMINATED,
           BLOCKED, UNKNOWN)


class AnticipationHorizon:
    NEXT_EVENT = "next_event"
    SHORT_WINDOW = "short_window"
    SAME_DAY = "same_day"
    UNKNOWN = "unknown"

    ALL = (NEXT_EVENT, SHORT_WINDOW, SAME_DAY, UNKNOWN)


@dataclass
class AnticipationCandidate:
    """One internal anticipation derived from a sign (prediction metadata only)."""

    anticipation_id: str
    anticipation_type: str
    sign_id: str
    linked_concept_ids: List[str] = field(default_factory=list)
    horizon: str = AnticipationHorizon.NEXT_EVENT
    detail: str = ""
    uncertainty: float = 1.0
    status: str = AnticipationStatus.PROPOSED
    contamination_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anticipation_id": self.anticipation_id,
            "anticipation_type": self.anticipation_type,
            "sign_id": self.sign_id,
            "linked_concept_ids": list(self.linked_concept_ids),
            "horizon": self.horizon, "detail": self.detail,
            "uncertainty": round(self.uncertainty, 3), "status": self.status,
            "contamination_findings": list(self.contamination_findings),
            "requests_data": False, "controls_feeders": False,
            "acts_in_world": False,
        }


@dataclass
class LiveAnticipationEngine:
    """Derives bounded, uncertainty-bearing anticipations from private signs."""

    def anticipate(self, *, signs: List[Any], load_status: str = "",
                   rhythm: Optional[Dict[str, Any]] = None,
                   max_anticipations: int = 200,
                   ) -> List[AnticipationCandidate]:
        rhythm = rhythm or {}
        rhythm_sources = {p.get("source_id", "")
                          for p in rhythm.get("patterns", []) or []
                          if p.get("kind") == "periodic"}
        out: List[AnticipationCandidate] = []
        for i, sign in enumerate(signs):
            if len(out) >= max_anticipations:
                break
            out.extend(self._for_sign(i, sign, load_status, rhythm_sources))
        return out

    def _for_sign(self, idx: int, sign: Any, load_status: str,
                  rhythm_sources: set) -> List[AnticipationCandidate]:
        sid = getattr(sign, "sign_id", f"sign_{idx}")
        concepts = list(getattr(sign, "linked_concept_ids", []) or [])
        sources = getattr(sign, "source_distribution", {}) or {}
        contamination = list(getattr(sign, "contamination_findings", []) or [])
        operator_only = (set(sources) == {"operator_pulse"} and bool(sources))
        out: List[AnticipationCandidate] = []

        def mk(atype, horizon, detail):
            a = AnticipationCandidate(
                anticipation_id=f"ant_{idx}_{atype}", anticipation_type=atype,
                sign_id=sid, linked_concept_ids=concepts, horizon=horizon,
                detail=detail, uncertainty=0.5,
                contamination_findings=list(contamination))
            # Anticipation from operator text alone is blocked / contaminated.
            if operator_only:
                a.status = AnticipationStatus.CONTAMINATED
                a.contamination_findings.append("operator_pulse_dominance")
                a.uncertainty = 1.0
                a.detail += " (operator-text-only; blocked)"
            elif contamination:
                a.status = AnticipationStatus.CONTAMINATED
                a.uncertainty = 0.9
            return a

        # Absence-linked sign -> silence likely continues.
        sig_refs = " ".join(getattr(sign, "supporting_refs", []) or [])
        if "absence" in sig_refs or "chronos_absence" in sources:
            out.append(mk(AnticipationType.SOURCE_SILENCE_CONTINUES,
                          AnticipationHorizon.SHORT_WINDOW,
                          "absence-linked sign anticipates continued silence"))
        # Rhythmic source -> rhythm continuation + recurrence.
        if rhythm_sources & set(sources):
            out.append(mk(AnticipationType.RHYTHM_CONTINUATION,
                          AnticipationHorizon.NEXT_EVENT,
                          "periodic source anticipates rhythm continuation"))
        out.append(mk(AnticipationType.RECURRENCE_EXPECTED,
                      AnticipationHorizon.SHORT_WINDOW,
                      "stable sign anticipates recurrence of its pattern"))
        # Multi-source sign -> co-occurrence.
        if len(sources) >= 2:
            out.append(mk(AnticipationType.CO_OCCURRENCE,
                          AnticipationHorizon.NEXT_EVENT,
                          "multi-source sign anticipates co-occurrence"))
        # Load context -> overload/deprivation risk.
        if "overload" in str(load_status):
            out.append(mk(AnticipationType.OVERLOAD_RISK,
                          AnticipationHorizon.SAME_DAY,
                          "load context anticipates overload risk"))
        elif "deprivation" in str(load_status):
            out.append(mk(AnticipationType.DEPRIVATION_RISK,
                          AnticipationHorizon.SAME_DAY,
                          "load context anticipates deprivation risk"))
        return out
