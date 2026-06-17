"""Sensory impression schema -- the first internal perceptual objects.

A :class:`SensoryImpression` is what downstream modules consume: an operational
boundary record produced by the membrane from a validated event. Raw events should
not be used directly by ontogenesis/semiogenesis/cognition once the membrane is
integrated. Debug gloss is preserved only as annotation (never grounding truth),
operator pulse is preserved as stimulus pressure (never teaching), and every
impression links to its source-event evidence.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SensoryImpressionKind:
    ENVIRONMENTAL_SCALAR = "environmental_scalar"
    MACHINE_BODY_PRESSURE = "machine_body_pressure"
    CHRONOS_TICK = "chronos_tick"
    ABSENCE = "absence"
    SOURCE_RHYTHM = "source_rhythm"
    SOURCE_NOISE = "source_noise"
    SOURCE_OVERLOAD = "source_overload"
    SOURCE_DEPRIVATION = "source_deprivation"
    PROJECT_FIELD_CHANGE = "project_field_change"
    OPERATOR_PULSE = "operator_pulse"
    QUARANTINE_SHADOW = "quarantine_shadow"
    UNKNOWN = "unknown"

    ALL = (ENVIRONMENTAL_SCALAR, MACHINE_BODY_PRESSURE, CHRONOS_TICK, ABSENCE,
           SOURCE_RHYTHM, SOURCE_NOISE, SOURCE_OVERLOAD, SOURCE_DEPRIVATION,
           PROJECT_FIELD_CHANGE, OPERATOR_PULSE, QUARANTINE_SHADOW, UNKNOWN)


class SensoryImpressionGrounding:
    FEATURE_BASED = "feature_based"
    SOURCE_BASED = "source_based"
    RHYTHM_BASED = "rhythm_based"
    ABSENCE_BASED = "absence_based"
    PRESSURE_BASED = "pressure_based"
    ANNOTATION_ONLY = "annotation_only"
    UNKNOWN = "unknown"

    ALL = (FEATURE_BASED, SOURCE_BASED, RHYTHM_BASED, ABSENCE_BASED,
           PRESSURE_BASED, ANNOTATION_ONLY, UNKNOWN)


@dataclass
class SensoryImpressionQuality:
    """Bounded quality descriptors for a sensory impression."""

    completeness: float = 1.0
    noise: float = 0.0
    confidence: float = 0.5
    is_noisy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"completeness": round(self.completeness, 3),
                "noise": round(self.noise, 3),
                "confidence": round(self.confidence, 3),
                "is_noisy": self.is_noisy}


@dataclass
class SensoryImpression:
    """One internal sensory impression produced by the membrane."""

    impression_id: str
    source_event_id: str
    timestamp_utc: str
    source_id: str
    receptor_id: str
    modality: str
    channel: str
    impression_kind: str = SensoryImpressionKind.UNKNOWN
    perceptual_intensity: float = 0.0
    salience: float = 0.0
    novelty: float = 0.0
    repetition: float = 0.0
    risk: float = 0.0
    contamination: float = 0.0
    source_pressure: float = 0.0
    absence_component: float = 0.0
    overload_component: float = 0.0
    deprivation_component: float = 0.0
    human_text_weight: float = 0.0
    operator_pulse_weight: float = 0.0
    debug_gloss_weight: float = 0.0
    grounding: str = SensoryImpressionGrounding.UNKNOWN
    quality: SensoryImpressionQuality = field(
        default_factory=SensoryImpressionQuality)
    permeability_status: str = "allow"
    evidence_refs: List[str] = field(default_factory=list)
    debug_gloss_annotation: str = ""  # annotation only; never grounding truth
    limitations: List[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.permeability_status in ("block", "quarantine")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impression_id": self.impression_id,
            "source_event_id": self.source_event_id,
            "timestamp_utc": self.timestamp_utc, "source_id": self.source_id,
            "receptor_id": self.receptor_id, "modality": self.modality,
            "channel": self.channel, "impression_kind": self.impression_kind,
            "perceptual_intensity": round(self.perceptual_intensity, 3),
            "salience": round(self.salience, 3),
            "novelty": round(self.novelty, 3),
            "repetition": round(self.repetition, 3),
            "risk": round(self.risk, 3),
            "contamination": round(self.contamination, 3),
            "source_pressure": round(self.source_pressure, 3),
            "absence_component": round(self.absence_component, 3),
            "overload_component": round(self.overload_component, 3),
            "deprivation_component": round(self.deprivation_component, 3),
            "human_text_weight": round(self.human_text_weight, 3),
            "operator_pulse_weight": round(self.operator_pulse_weight, 3),
            "debug_gloss_weight": round(self.debug_gloss_weight, 3),
            "grounding": self.grounding, "quality": self.quality.to_dict(),
            "permeability_status": self.permeability_status,
            "blocked": self.blocked,
            "evidence_refs": list(self.evidence_refs),
            "debug_gloss_annotation": self.debug_gloss_annotation,
            "debug_gloss_is_ground_truth": False,
            "operator_pulse_is_teaching": False,
            "limitations": list(self.limitations),
        }


@dataclass
class SensoryImpressionStore:
    """Persists sensory impressions as local boundary records."""

    state_dir: str = ".solaris_ai_nn_live"
    impressions: List[SensoryImpression] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "membrane", "impressions")

    @property
    def jsonl_path(self) -> str:
        return os.path.join(self._dir, "SENSORY_IMPRESSIONS.jsonl")

    @property
    def index_json_path(self) -> str:
        return os.path.join(self._dir, "SENSORY_IMPRESSION_INDEX.json")

    @property
    def index_md_path(self) -> str:
        return os.path.join(self._dir, "SENSORY_IMPRESSION_INDEX.md")

    def add(self, impression: SensoryImpression) -> SensoryImpression:
        self.impressions.append(impression)
        return impression

    def index(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for imp in self.impressions:
            kinds[imp.impression_kind] = kinds.get(imp.impression_kind, 0) + 1
            statuses[imp.permeability_status] = statuses.get(
                imp.permeability_status, 0) + 1
        return {
            "membrane_impression_count": len(self.impressions),
            "by_kind": kinds, "by_permeability_status": statuses,
            "blocked_impression_count": sum(1 for i in self.impressions
                                            if i.blocked),
            "note": "sensory impressions are the first internal perceptual "
                    "objects; downstream modules should consume impressions, not "
                    "raw events; debug gloss is annotation only; they are "
                    "operational boundary records, not evidence of consciousness",
        }

    def write(self) -> Dict[str, str]:
        os.makedirs(self._dir, exist_ok=True)
        with open(self.jsonl_path, "w", encoding="utf-8") as fh:
            for imp in self.impressions:
                fh.write(json.dumps(imp.to_dict(), default=str) + "\n")
        with open(self.index_json_path, "w", encoding="utf-8") as fh:
            json.dump(self.index(), fh, indent=2, default=str)
        with open(self.index_md_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_md())
        return {"jsonl": self.jsonl_path, "index_json": self.index_json_path,
                "index_md": self.index_md_path}

    def _render_md(self) -> str:
        idx = self.index()
        lines = ["# Sensory Impression Index", "",
                 f"- impressions: {idx['membrane_impression_count']}",
                 f"- by kind: {idx['by_kind']}",
                 f"- by permeability status: {idx['by_permeability_status']}",
                 f"- blocked: {idx['blocked_impression_count']}", "",
                 "| impression | kind | receptor | status | salience | risk |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for imp in self.impressions[:200]:
            lines.append(f"| {imp.impression_id} | {imp.impression_kind} | "
                         f"{imp.receptor_id} | {imp.permeability_status} | "
                         f"{imp.salience:.2f} | {imp.risk:.2f} |")
        lines += ["", "_Sensory impressions are operational boundary records, not "
                  "evidence of consciousness, life, or agency. Debug gloss is "
                  "annotation only; operator pulse is stimulus, not teaching._"]
        return "\n".join(lines) + "\n"
