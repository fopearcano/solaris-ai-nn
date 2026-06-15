"""Boundary tensions -- self/world ambiguities that feed LOGOS, kept unresolved.

The :class:`BoundaryTensionDetector` surfaces operational tensions at the self/world
boundary (internal vs external, simulation vs observation, memory vs current flux,
prediction vs sensory event, etc.). Tensions feed LOGOS; ambiguous tensions are not
resolved prematurely, and unknown-origin tensions remain visible.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class BoundaryTensionType:
    INTERNAL_VS_EXTERNAL = "internal_vs_external"
    SIMULATION_VS_OBSERVATION = "simulation_vs_observation"
    MEMORY_VS_CURRENT_FLUX = "memory_vs_current_flux"
    PREDICTION_VS_SENSORY_EVENT = "prediction_vs_sensory_event"
    ANNOTATION_VS_FEATURE_EVIDENCE = "operator_annotation_vs_feature_evidence"
    FEEDER_ARTIFACT_VS_WORLD_SOURCE = "feeder_artifact_vs_world_source"
    RECEPTOR_BODY_VS_EXTERNAL_SOURCE = "receptor_body_vs_external_source"
    SELF_CONTINUITY_VS_RESTART_GAP = "self_continuity_vs_restart_gap"
    HUMAN_GLOSS_VS_INTERNAL_SIGN = "human_gloss_vs_internal_sign"
    UNKNOWN_ORIGIN = "unknown_origin"

    ALL = (INTERNAL_VS_EXTERNAL, SIMULATION_VS_OBSERVATION,
           MEMORY_VS_CURRENT_FLUX, PREDICTION_VS_SENSORY_EVENT,
           ANNOTATION_VS_FEATURE_EVIDENCE, FEEDER_ARTIFACT_VS_WORLD_SOURCE,
           RECEPTOR_BODY_VS_EXTERNAL_SOURCE, SELF_CONTINUITY_VS_RESTART_GAP,
           HUMAN_GLOSS_VS_INTERNAL_SIGN, UNKNOWN_ORIGIN)


@dataclass
class BoundaryTension:
    """One operational boundary tension (feeds LOGOS; kept unresolved if unclear)."""

    tension_type: str
    refs: List[str] = field(default_factory=list)
    tension_id: str = field(default_factory=lambda: f"BTN_{uuid.uuid4().hex[:8]}")
    intensity: float = 0.0
    resolved: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tension_id": self.tension_id,
            "tension_type": self.tension_type,
            "refs": list(self.refs),
            "intensity": round(self.intensity, 4),
            "resolved": self.resolved,
            "detail": self.detail,
            "note": "boundary tension; unknown-origin tensions remain visible",
        }


@dataclass
class BoundaryTensionDetector:
    """Detects boundary tensions from ownership / classification / continuity."""

    tensions: List[BoundaryTension] = field(default_factory=list)

    def detect(self, *, ownership: Any, classifier: Any,
               simulation: Any, continuity: Any,
               source_attribution: Any) -> List[BoundaryTension]:
        self.tensions = []

        # internal vs external: both present in the classifier's mixed records.
        if getattr(classifier, "mixed", lambda: [])():
            self._add(BoundaryTensionType.INTERNAL_VS_EXTERNAL,
                      intensity=0.4, detail="mixed internal/external records")
        # simulation vs observation: any boundary violation OR sim markers present.
        if getattr(simulation, "violations", []):
            self._add(BoundaryTensionType.SIMULATION_VS_OBSERVATION,
                      intensity=0.7, detail="simulation boundary violation")
        elif any(m.marker in ("simulation", "counterfactual")
                 for m in getattr(simulation, "markers", [])):
            self._add(BoundaryTensionType.SIMULATION_VS_OBSERVATION,
                      intensity=0.3, detail="simulated state alongside observation")
        # feeder artifact vs world source: feeder + world both attributed.
        targets = {a.target for a in getattr(source_attribution,
                                             "attributions", [])}
        if "feeder_artifact" in targets and "external_source" in targets:
            self._add(BoundaryTensionType.FEEDER_ARTIFACT_VS_WORLD_SOURCE,
                      intensity=0.4, detail="feeder artifact vs world source")
        # receptor body vs external source.
        if any(a.ownership_type == "self_receptor_state"
               for a in getattr(ownership, "attributions", [])) and \
                any(a.ownership_type == "external_source"
                    for a in getattr(ownership, "attributions", [])):
            self._add(BoundaryTensionType.RECEPTOR_BODY_VS_EXTERNAL_SOURCE,
                      intensity=0.3, detail="receptor body vs external source")
        # self continuity vs restart gap.
        if any(not b.recovered for b in getattr(continuity, "breaks", [])):
            self._add(BoundaryTensionType.SELF_CONTINUITY_VS_RESTART_GAP,
                      intensity=0.5, detail="unrecovered continuity break")
        # human gloss vs internal sign.
        if any(a.target == "human_annotation"
               for a in getattr(source_attribution, "attributions", [])):
            self._add(BoundaryTensionType.HUMAN_GLOSS_VS_INTERNAL_SIGN,
                      intensity=0.3, detail="human gloss alongside internal sign")
        # unknown origin: any unknown ownership remains visible.
        if getattr(ownership, "ambiguous", lambda: [])():
            self._add(BoundaryTensionType.UNKNOWN_ORIGIN, intensity=0.2,
                      detail="ambiguous/unknown ownership preserved")
        return self.tensions

    def _add(self, tension_type: str, *, intensity: float,
             detail: str) -> None:
        self.tensions.append(BoundaryTension(
            tension_type=tension_type, intensity=intensity, detail=detail))

    def to_dict(self) -> Dict[str, Any]:
        return {"tension_count": len(self.tensions),
                "tensions": [t.to_dict() for t in self.tensions]}
