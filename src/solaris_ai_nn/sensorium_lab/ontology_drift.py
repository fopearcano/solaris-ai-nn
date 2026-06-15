"""Ontology drift -- which way did the internal categories lean?

An :class:`OntologyDriftDetector` measures whether the categories Solaris formed
under a sensorium drifted toward a human object ontology, a modality-native
ontology, a cross-modal field ontology, a machine-rhythm ontology, an
absence/rhythm ontology, or a label-contaminated ontology. Human ontology is not
forbidden -- but it must not silently dominate, so drift toward human labels is
measured and reported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class OntologyKind:
    HUMAN_OBJECT = "human_object_ontology"
    MODALITY_NATIVE = "modality_native_ontology"
    CROSS_MODAL_FIELD = "cross_modal_field_ontology"
    MACHINE_RHYTHM = "machine_rhythm_ontology"
    ABSENCE_RHYTHM = "absence_rhythm_ontology"
    LABEL_CONTAMINATED = "label_contaminated_ontology"

    ALL = (HUMAN_OBJECT, MODALITY_NATIVE, CROSS_MODAL_FIELD, MACHINE_RHYTHM,
           ABSENCE_RHYTHM, LABEL_CONTAMINATED)


@dataclass
class OntologyDrift:
    """A single drift weight toward one ontology kind."""

    kind: str
    weight: float
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OntologyDriftResult:
    dominant_ontology: str
    drift_score: float
    weights: Dict[str, float] = field(default_factory=dict)
    drifts: List[OntologyDrift] = field(default_factory=list)
    human_label_contamination_score: float = 0.0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dominant_ontology": self.dominant_ontology,
            "drift_score": self.drift_score,
            "weights": dict(self.weights),
            "drifts": [d.to_dict() for d in self.drifts],
            "human_label_contamination_score":
                self.human_label_contamination_score,
            "notes": list(self.notes),
            "note": "human ontology is not forbidden, but it must not silently "
                    "dominate; drift toward labels is measured, not hidden",
        }


@dataclass
class OntologyDriftDetector:
    """Measures which ontology the internal categories drifted toward."""

    def detect(self, runtime: Any) -> OntologyDriftResult:
        if runtime is None:
            return OntologyDriftResult(
                dominant_ontology=OntologyKind.MODALITY_NATIVE, drift_score=0.0,
                notes=["no runtime; drift inconclusive"])
        rt = runtime
        weights: Dict[str, float] = {k: 0.0 for k in OntologyKind.ALL}
        drifts: List[OntologyDrift] = []

        protos = rt.proto_symbol_candidates
        total = max(1, len(protos))
        contaminated = sum(1 for p in protos
                           if p.get("human_label_contaminated"))
        human_text = sum(1 for p in protos
                         if p.get("modality") == "human_textual")
        machine = sum(1 for p in protos
                      if p.get("modality") == "machine_rhythm")
        cross = sum(1 for p in protos
                    if p.get("symbol_type") == "cross_modal_symbol")
        absence_sym = sum(1 for p in protos
                          if p.get("symbol_type") == "absence_grounded_symbol")
        native = total - contaminated - human_text

        contamination_score = rt.human_label_contamination_score()

        weights[OntologyKind.MODALITY_NATIVE] = native / total
        weights[OntologyKind.HUMAN_OBJECT] = human_text / total
        weights[OntologyKind.LABEL_CONTAMINATED] = max(
            contaminated / total, contamination_score)
        weights[OntologyKind.CROSS_MODAL_FIELD] = (
            min(1.0, rt.cross_modal.relation_count() / max(1, total)) * 0.5
            + (cross / total) * 0.5)
        weights[OntologyKind.MACHINE_RHYTHM] = machine / total
        weights[OntologyKind.ABSENCE_RHYTHM] = max(
            absence_sym / total,
            min(1.0, len(rt.absence.events) / 5.0) * 0.5)

        for kind, weight in weights.items():
            if weight > 0:
                drifts.append(OntologyDrift(kind=kind, weight=round(weight, 4)))

        dominant = max(weights, key=weights.get)
        drift_score = round(weights[dominant], 4)
        notes: List[str] = []
        if weights[OntologyKind.LABEL_CONTAMINATED] > 0.3:
            notes.append("categories drifted toward human labels; "
                         "contamination is significant and is reported")
        if dominant == OntologyKind.MODALITY_NATIVE:
            notes.append("categories are modality-native (not human-object)")
        return OntologyDriftResult(
            dominant_ontology=dominant, drift_score=drift_score,
            weights={k: round(v, 4) for k, v in weights.items()},
            drifts=drifts,
            human_label_contamination_score=contamination_score, notes=notes)
