"""Membrane contamination analysis -- recorded even when an event is allowed.

:class:`MembraneContaminationAssessment` inspects a validated event for
contamination: human-label/debug-gloss ground-truth attempts, operator-pulse and
human-text dominance, command-like text, private data, secret markers, forbidden or
unknown sources, fixture-marker leakage, source/reporting artifacts, and unsupported
claim text. Contamination is recorded even when an event is allowed-attenuated, high
contamination blocks or quarantines, and the score propagates to sensory impressions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..live_birth.birth_profile import (
    ALLOWED_FIRST_BIRTH_SOURCES,
    FORBIDDEN_FIRST_BIRTH_SOURCES,
)

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")
_SECRET_MARKERS = ("password", "secret", "api key", "api_key", "credential",
                   "token=", "private message")
_COMMAND_MARKERS = ("execute:", "run:", "sudo ", "rm -", "shell:", "command:",
                    "do this", "you must")
_FIXTURE_MARKERS = ("fixture", "gold_label", "ground_truth_label", "test_label")
_CLAIM_MARKERS = ("is conscious", "is alive", "is sentient", "has agency",
                  "free will", "self-aware")


class MembraneContaminationType:
    HUMAN_LABEL_GROUND_TRUTH = "human_label_ground_truth_attempt"
    DEBUG_GLOSS_GROUND_TRUTH = "debug_gloss_ground_truth_attempt"
    OPERATOR_PULSE_DOMINANCE = "operator_pulse_dominance"
    HUMAN_TEXT_DOMINANCE = "human_text_dominance"
    COMMAND_LIKE_TEXT = "command_like_text"
    PRIVATE_DATA = "private_data"
    SECRET_MARKER = "secret_marker"
    FORBIDDEN_SOURCE = "forbidden_source"
    UNKNOWN_SOURCE = "unknown_source"
    FIXTURE_MARKER_LEAKAGE = "fixture_marker_leakage"
    SOURCE_ARTIFACT = "source_artifact"
    REPORTING_ARTIFACT = "reporting_artifact"
    UNSUPPORTED_CLAIM_TEXT = "unsupported_claim_text"
    UNKNOWN = "unknown"

    ALL = (HUMAN_LABEL_GROUND_TRUTH, DEBUG_GLOSS_GROUND_TRUTH,
           OPERATOR_PULSE_DOMINANCE, HUMAN_TEXT_DOMINANCE, COMMAND_LIKE_TEXT,
           PRIVATE_DATA, SECRET_MARKER, FORBIDDEN_SOURCE, UNKNOWN_SOURCE,
           FIXTURE_MARKER_LEAKAGE, SOURCE_ARTIFACT, REPORTING_ARTIFACT,
           UNSUPPORTED_CLAIM_TEXT, UNKNOWN)

# Types that force block/quarantine regardless of attenuation.
_BLOCKING = frozenset({
    MembraneContaminationType.HUMAN_LABEL_GROUND_TRUTH,
    MembraneContaminationType.DEBUG_GLOSS_GROUND_TRUTH,
    MembraneContaminationType.COMMAND_LIKE_TEXT,
    MembraneContaminationType.PRIVATE_DATA,
    MembraneContaminationType.SECRET_MARKER,
    MembraneContaminationType.FORBIDDEN_SOURCE,
})


@dataclass
class MembraneContaminationFinding:
    """One contamination finding (always recorded, never hidden)."""

    contamination_type: str
    detail: str = ""
    blocks: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"contamination_type": self.contamination_type,
                "detail": self.detail, "blocks": self.blocks}


@dataclass
class MembraneContaminationAssessment:
    """The contamination findings for one event + an aggregate score."""

    event_id: str
    source_id: str
    findings: List[MembraneContaminationFinding] = field(default_factory=list)

    @property
    def score(self) -> float:
        if not self.findings:
            return 0.0
        weight = sum(1.0 if f.blocks else 0.4 for f in self.findings)
        return min(1.0, weight / 2.0)

    @property
    def blocks(self) -> bool:
        return any(f.blocks for f in self.findings)

    @property
    def types(self) -> List[str]:
        return [f.contamination_type for f in self.findings]

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "contamination_score": round(self.score, 3),
                "blocks": self.blocks, "finding_count": len(self.findings),
                "findings": [f.to_dict() for f in self.findings]}


@dataclass
class MembraneContaminationAnalyzer:
    """Assesses contamination of a single validated event."""

    def evaluate(self, event: Dict[str, Any], *,
                 source_pressure: Dict[str, Any] = None,
                 ) -> MembraneContaminationAssessment:
        import json as _json

        source_pressure = source_pressure or {}
        eid = str(event.get("event_id", ""))
        sid = str(event.get("source_id", ""))
        a = MembraneContaminationAssessment(event_id=eid, source_id=sid)

        def add(t, detail, blocks=False):
            a.findings.append(MembraneContaminationFinding(
                t, detail, blocks=blocks or t in _BLOCKING))

        if event.get("human_label_is_ground_truth"):
            add(MembraneContaminationType.HUMAN_LABEL_GROUND_TRUTH,
                "event asserts human_label_is_ground_truth")
        if event.get("debug_gloss_is_ground_truth"):
            add(MembraneContaminationType.DEBUG_GLOSS_GROUND_TRUTH,
                "event asserts debug_gloss_is_ground_truth")
        safety = event.get("safety", {}) or {}
        if safety.get("contains_secret"):
            add(MembraneContaminationType.SECRET_MARKER, "contains_secret flag")
        if safety.get("private_data"):
            add(MembraneContaminationType.PRIVATE_DATA, "private_data flag")
        if safety.get("contains_instruction") or event.get("is_command"):
            add(MembraneContaminationType.COMMAND_LIKE_TEXT,
                "instruction/command flagged")

        if sid in FORBIDDEN_FIRST_BIRTH_SOURCES:
            add(MembraneContaminationType.FORBIDDEN_SOURCE,
                f"source {sid!r} is forbidden")
        elif sid not in ALLOWED_FIRST_BIRTH_SOURCES:
            add(MembraneContaminationType.UNKNOWN_SOURCE,
                f"source {sid!r} is not in the allowed set")

        # Scan payload values + gloss + channel text only -- never the event's
        # own safety-flag key names (e.g. "contains_secret") which would
        # false-positive on every clean event.
        blob = " ".join([
            _json.dumps(event.get("payload"), default=str),
            str(event.get("debug_gloss", "")),
            str(event.get("channel", "")),
            str(event.get("privacy_notes", "")),
        ]).lower()
        if any(m in blob for m in _SECRET_MARKERS):
            add(MembraneContaminationType.SECRET_MARKER,
                "secret marker present in event text")
        if any(m in blob for m in _COMMAND_MARKERS):
            add(MembraneContaminationType.COMMAND_LIKE_TEXT,
                "command-like text present in event")
        if any(m in blob for m in _FIXTURE_MARKERS):
            add(MembraneContaminationType.FIXTURE_MARKER_LEAKAGE,
                "fixture/label marker present in event")
        gloss = str(event.get("debug_gloss", "")).lower()
        if any(m in gloss for m in _CLAIM_MARKERS) and " not " not in gloss \
                and " no " not in gloss:
            add(MembraneContaminationType.UNSUPPORTED_CLAIM_TEXT,
                "unsupported claim text in debug gloss")

        # Dominance contamination from the source-pressure context.
        if source_pressure.get("membrane_operator_dominance_score", 0.0) >= 0.4 \
                and sid == _OPERATOR_PULSE:
            add(MembraneContaminationType.OPERATOR_PULSE_DOMINANCE,
                "operator pulse dominates the boundary")
        if source_pressure.get("human_text_dominance_score", 0.0) >= 0.5 \
                and sid in _HUMAN_TEXT_SOURCES:
            add(MembraneContaminationType.HUMAN_TEXT_DOMINANCE,
                "human-text sources dominate the boundary")
        return a

    @staticmethod
    def summary(assessments: List[MembraneContaminationAssessment],
                ) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for a in assessments:
            for f in a.findings:
                types[f.contamination_type] = types.get(
                    f.contamination_type, 0) + 1
        return {
            "membrane_contamination_count": sum(len(a.findings)
                                                for a in assessments),
            "contaminated_event_count": sum(1 for a in assessments
                                            if a.findings),
            "blocking_event_count": sum(1 for a in assessments if a.blocks),
            "contamination_types": types,
            "note": "contamination is recorded even when an event is allowed "
                    "attenuated; high contamination blocks or quarantines; "
                    "scores propagate to sensory impressions",
        }
