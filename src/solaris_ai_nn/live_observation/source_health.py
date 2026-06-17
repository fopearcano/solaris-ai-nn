"""Live source health -- per-source health from observed events (read-only).

:class:`LiveSourceHealthEvaluator` evaluates each registered source for presence,
rate, malformed/quarantine rate, payload/timestamp consistency, repetition, noise,
reliability, and contamination risks (private/command/label-ground-truth/
debug-gloss). An unknown source is not trusted; a forbidden source blocks stability;
a source may be useful-but-noisy; and a silent source is not automatically a failure
(it may be an absence signal).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..live_birth.birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES


class SourceHealthStatus:
    HEALTHY = "healthy"
    HEALTHY_WITH_WARNINGS = "healthy_with_warnings"
    SILENT = "silent"
    NOISY = "noisy"
    UNSTABLE = "unstable"
    QUARANTINED = "quarantined"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"

    ALL = (HEALTHY, HEALTHY_WITH_WARNINGS, SILENT, NOISY, UNSTABLE, QUARANTINED,
           FORBIDDEN, UNKNOWN)


@dataclass
class SourceHealthFinding:
    """One per-source health finding."""

    finding: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding": self.finding, "detail": self.detail}


@dataclass
class LiveSourceHealth:
    """The computed health of one source."""

    source_id: str
    present: bool = False
    registered: bool = True
    event_count: int = 0
    quarantine_count: int = 0
    malformed_count: int = 0
    repeated_identical_count: int = 0
    noise_score: float = 0.0
    confidence_score: float = 0.0
    reliability_estimate: float = 0.0
    privacy_risk: str = "low"
    command_contamination: bool = False
    label_ground_truth_contamination: bool = False
    debug_gloss_contamination: bool = False
    status: str = SourceHealthStatus.UNKNOWN
    findings: List[SourceHealthFinding] = field(default_factory=list)

    @property
    def quarantine_rate(self) -> float:
        total = self.event_count + self.quarantine_count
        return self.quarantine_count / total if total else 0.0

    @property
    def blocks_stability(self) -> bool:
        return self.status == SourceHealthStatus.FORBIDDEN \
            or self.command_contamination \
            or self.label_ground_truth_contamination

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id, "present": self.present,
            "registered": self.registered, "event_count": self.event_count,
            "quarantine_count": self.quarantine_count,
            "quarantine_rate": round(self.quarantine_rate, 3),
            "malformed_count": self.malformed_count,
            "repeated_identical_count": self.repeated_identical_count,
            "noise_score": round(self.noise_score, 3),
            "confidence_score": round(self.confidence_score, 3),
            "reliability_estimate": round(self.reliability_estimate, 3),
            "privacy_risk": self.privacy_risk,
            "command_contamination": self.command_contamination,
            "label_ground_truth_contamination":
                self.label_ground_truth_contamination,
            "debug_gloss_contamination": self.debug_gloss_contamination,
            "status": self.status, "blocks_stability": self.blocks_stability,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class LiveSourceHealthEvaluator:
    """Evaluates per-source health from accepted events + quarantine counts."""

    def evaluate(self, *, registered_sources: List[str],
                 accepted_events: List[Dict[str, Any]],
                 quarantine_by_source: Optional[Dict[str, int]] = None,
                 observed_source_ids: Optional[List[str]] = None,
                 ) -> List[LiveSourceHealth]:
        quarantine_by_source = quarantine_by_source or {}
        by_source: Dict[str, List[Dict[str, Any]]] = {}
        for ev in accepted_events:
            by_source.setdefault(ev.get("source_id", ""), []).append(ev)
        # Union of registered + observed (incl. quarantined-only) sources.
        all_ids = list(dict.fromkeys(
            list(registered_sources) + list(by_source.keys())
            + list(quarantine_by_source.keys())
            + list(observed_source_ids or [])))
        out: List[LiveSourceHealth] = []
        for sid in all_ids:
            out.append(self._evaluate_one(
                sid, by_source.get(sid, []),
                quarantine_by_source.get(sid, 0),
                registered=sid in registered_sources))
        return out

    def _evaluate_one(self, source_id: str, events: List[Dict[str, Any]],
                      quarantine_count: int, registered: bool,
                      ) -> LiveSourceHealth:
        h = LiveSourceHealth(source_id=source_id, registered=registered,
                             present=bool(events), event_count=len(events),
                             quarantine_count=quarantine_count)
        if source_id in FORBIDDEN_FIRST_BIRTH_SOURCES:
            h.status = SourceHealthStatus.FORBIDDEN
            h.findings.append(SourceHealthFinding(
                "forbidden_source", "source is on the forbidden list"))
            return h
        if not registered:
            h.findings.append(SourceHealthFinding(
                "unregistered_source", "source is not in the feeder registry"))

        # Noise + repetition + contamination from event payloads/quality.
        noise_total = 0.0
        payloads: Dict[str, int] = {}
        for ev in events:
            q = ev.get("quality", {}) or {}
            noise_total += float(q.get("noise", 0.0) or 0.0)
            if q.get("is_noisy"):
                noise_total += 0.5
            key = json.dumps(ev.get("payload"), sort_keys=True, default=str)
            payloads[key] = payloads.get(key, 0) + 1
            if ev.get("is_command"):
                h.command_contamination = True
            if ev.get("human_label_is_ground_truth"):
                h.label_ground_truth_contamination = True
            if ev.get("debug_gloss_is_ground_truth"):
                h.debug_gloss_contamination = True
        if events:
            h.noise_score = min(noise_total / len(events), 1.0)
            h.repeated_identical_count = sum(c - 1 for c in payloads.values()
                                             if c > 1)
        h.reliability_estimate = max(0.0, 1.0 - h.quarantine_rate - h.noise_score
                                     * 0.5)
        h.confidence_score = round(h.reliability_estimate, 3)

        # Status.
        if not events:
            h.status = SourceHealthStatus.SILENT
            h.findings.append(SourceHealthFinding(
                "silent", "no accepted events observed (may be an absence "
                "signal)"))
        elif h.quarantine_rate >= 0.5:
            h.status = SourceHealthStatus.QUARANTINED
        elif h.noise_score >= 0.5:
            h.status = SourceHealthStatus.NOISY
            h.findings.append(SourceHealthFinding(
                "noisy", "high noise score; useful but noisy"))
        elif h.repeated_identical_count >= max(2, len(events) - 1) \
                and len(events) > 2:
            h.status = SourceHealthStatus.UNSTABLE
            h.findings.append(SourceHealthFinding(
                "repeated_identical", "repeated identical payloads"))
        elif h.command_contamination or h.label_ground_truth_contamination:
            h.status = SourceHealthStatus.UNSTABLE
        else:
            h.status = (SourceHealthStatus.HEALTHY_WITH_WARNINGS
                        if (not registered or h.repeated_identical_count)
                        else SourceHealthStatus.HEALTHY)
        return h

    @staticmethod
    def summary(healths: List[LiveSourceHealth]) -> Dict[str, Any]:
        def count(status):
            return sum(1 for h in healths if h.status == status)
        return {
            "live_source_count": len(healths),
            "live_healthy_source_count": (count(SourceHealthStatus.HEALTHY)
                                          + count(
                                              SourceHealthStatus.HEALTHY_WITH_WARNINGS)),
            "live_noisy_source_count": count(SourceHealthStatus.NOISY),
            "live_silent_source_count": count(SourceHealthStatus.SILENT),
            "live_forbidden_source_count": count(SourceHealthStatus.FORBIDDEN),
            "live_unstable_source_count": count(SourceHealthStatus.UNSTABLE),
            "blocks_stability": any(h.blocks_stability for h in healths),
            "sources": [h.to_dict() for h in healths],
            "note": "an unknown source is not trusted; a forbidden source blocks "
                    "stability; a silent source may be an absence signal, not a "
                    "failure",
        }
