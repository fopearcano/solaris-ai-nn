"""Membrane source pressure -- how hard each source is pushing on the boundary.

:class:`MembraneSourcePressure` measures per-source event/accepted/blocked/
quarantined rates, source and modality dominance, operator-pulse and human-text
dominance, debug-gloss density, repetition/burst/silence pressure, missing expected
sources, and trust/toxicity drift. Source pressure informs permeability but never
modifies feeders; recommendations are report-only and dominance is always visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")


class SourcePressureStatus:
    BALANCED = "balanced"
    DOMINANT = "dominant"
    OVERACTIVE = "overactive"
    SILENT = "silent"
    DEPRIVED = "deprived"
    NOISY = "noisy"
    TOXIC = "toxic"
    OPERATOR_DOMINATED = "operator_dominated"
    HUMAN_TEXT_DOMINATED = "human_text_dominated"
    UNKNOWN = "unknown"

    ALL = (BALANCED, DOMINANT, OVERACTIVE, SILENT, DEPRIVED, NOISY, TOXIC,
           OPERATOR_DOMINATED, HUMAN_TEXT_DOMINATED, UNKNOWN)


@dataclass
class SourcePressureAssessment:
    """The full source-pressure assessment over a batch of events."""

    total_events: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)
    by_modality: Dict[str, int] = field(default_factory=dict)
    blocked_by_source: Dict[str, int] = field(default_factory=dict)
    quarantined_by_source: Dict[str, int] = field(default_factory=dict)
    dominance_score: float = 0.0
    dominant_source: str = ""
    operator_dominance_score: float = 0.0
    human_text_dominance_score: float = 0.0
    debug_gloss_density: float = 0.0
    repeated_payload_pressure: int = 0
    status: str = SourcePressureStatus.UNKNOWN
    per_source_status: Dict[str, str] = field(default_factory=dict)
    missing_expected_sources: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        n = max(1, self.total_events)
        return {
            "total_events": self.total_events,
            "by_source": {k: round(v / n, 3)
                          for k, v in self.by_source.items()},
            "by_modality": {k: round(v / n, 3)
                            for k, v in self.by_modality.items()},
            "membrane_source_pressure_dominance_score": round(
                self.dominance_score, 3),
            "membrane_operator_dominance_score": round(
                self.operator_dominance_score, 3),
            "human_text_dominance_score": round(
                self.human_text_dominance_score, 3),
            "debug_gloss_density": round(self.debug_gloss_density, 3),
            "repeated_payload_pressure": self.repeated_payload_pressure,
            "dominant_source": self.dominant_source,
            "status": self.status,
            "per_source_status": dict(self.per_source_status),
            "missing_expected_sources": list(self.missing_expected_sources),
            "findings": list(self.findings),
            "note": "source pressure informs permeability but never modifies "
                    "feeders; recommendations are report-only; dominance is "
                    "always visible",
        }


@dataclass
class MembraneSourcePressure:
    """Computes source pressure from accepted events + receptor matches."""

    dominance_threshold: float = 0.6
    operator_threshold: float = 0.4
    human_text_threshold: float = 0.5

    def assess(self, *, events: List[Dict[str, Any]],
               blocked: Optional[Dict[str, int]] = None,
               quarantined: Optional[Dict[str, int]] = None,
               expected_sources: Optional[List[str]] = None,
               ) -> SourcePressureAssessment:
        a = SourcePressureAssessment(total_events=len(events))
        a.blocked_by_source = dict(blocked or {})
        a.quarantined_by_source = dict(quarantined or {})
        payloads: Dict[str, int] = {}
        gloss_count = 0
        import json as _json
        for ev in events:
            sid = str(ev.get("source_id", ""))
            a.by_source[sid] = a.by_source.get(sid, 0) + 1
            mod = str(ev.get("modality", ""))
            a.by_modality[mod] = a.by_modality.get(mod, 0) + 1
            if str(ev.get("debug_gloss", "")).strip():
                gloss_count += 1
            key = sid + "|" + _json.dumps(ev.get("payload"), sort_keys=True,
                                          default=str)
            payloads[key] = payloads.get(key, 0) + 1
        n = max(1, len(events))
        if a.by_source:
            a.dominant_source = max(a.by_source, key=a.by_source.get)
            a.dominance_score = a.by_source[a.dominant_source] / n
        a.operator_dominance_score = a.by_source.get(_OPERATOR_PULSE, 0) / n
        a.human_text_dominance_score = sum(
            a.by_source.get(s, 0) for s in _HUMAN_TEXT_SOURCES) / n
        a.debug_gloss_density = gloss_count / n
        a.repeated_payload_pressure = sum(c - 1 for c in payloads.values()
                                          if c > 1)

        expected = expected_sources or []
        a.missing_expected_sources = [s for s in expected
                                      if s not in a.by_source]
        a.per_source_status = self._per_source_status(a, n)
        a.status = self._overall_status(a)
        return a

    def _per_source_status(self, a: SourcePressureAssessment, n: int,
                           ) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for sid, count in a.by_source.items():
            share = count / n
            blocked = a.blocked_by_source.get(sid, 0)
            quarantined = a.quarantined_by_source.get(sid, 0)
            if quarantined and quarantined >= max(1, count):
                out[sid] = SourcePressureStatus.TOXIC
            elif sid == _OPERATOR_PULSE and share >= self.operator_threshold:
                out[sid] = SourcePressureStatus.OPERATOR_DOMINATED
            elif share >= self.dominance_threshold:
                out[sid] = SourcePressureStatus.DOMINANT
            else:
                out[sid] = SourcePressureStatus.BALANCED
        for sid in a.missing_expected_sources:
            out[sid] = SourcePressureStatus.SILENT
        return out

    def _overall_status(self, a: SourcePressureAssessment) -> str:
        if a.total_events == 0:
            return SourcePressureStatus.DEPRIVED
        if a.operator_dominance_score >= self.operator_threshold:
            a.findings.append("operator pulse dominates the boundary")
            return SourcePressureStatus.OPERATOR_DOMINATED
        if a.human_text_dominance_score >= self.human_text_threshold:
            a.findings.append("human-text sources dominate the boundary")
            return SourcePressureStatus.HUMAN_TEXT_DOMINATED
        if a.dominance_score >= self.dominance_threshold:
            a.findings.append(
                f"{a.dominant_source!r} dominates the boundary "
                f"({a.dominance_score:.0%})")
            return SourcePressureStatus.DOMINANT
        if a.missing_expected_sources:
            a.findings.append("expected source(s) silent")
            return SourcePressureStatus.DEPRIVED
        return SourcePressureStatus.BALANCED
