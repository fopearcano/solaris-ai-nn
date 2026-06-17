"""Live concept input -- load eligible proto-concepts from live ontogenesis.

:class:`ConceptInputLoader` reads the Prompt 69 live concept memory and ontogenesis
reports and returns the proto-concepts eligible to receive private signs. Only born
or stable proto-concepts are eligible by default; contaminated concepts are not
eligible; rejected concepts are not eligible but remain visible as counterevidence;
and human labels / debug gloss are loaded only as non-ground-truth annotations.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_ELIGIBLE_STATUSES = ("born", "stable_candidate")
_COUNTEREVIDENCE_STATUSES = ("rejected", "weak", "suspended")


class ConceptInputStatus:
    LOADED = "loaded"
    MISSING_CONCEPT_MEMORY = "missing_concept_memory"
    NO_ELIGIBLE_CONCEPTS = "no_eligible_concepts"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"

    ALL = (LOADED, MISSING_CONCEPT_MEMORY, NO_ELIGIBLE_CONCEPTS, SYNTHETIC,
           UNKNOWN)


@dataclass
class LiveConceptInput:
    """One eligible (or context) proto-concept loaded for semiogenesis."""

    concept_id: str
    feature_signature: str
    status: str
    stability_score: float = 0.0
    recurrence_count: int = 0
    source_distribution: Dict[str, int] = field(default_factory=dict)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    supporting_event_ids: List[str] = field(default_factory=list)
    contradicting_event_ids: List[str] = field(default_factory=list)
    contamination_findings: List[str] = field(default_factory=list)
    eligible: bool = False
    is_counterevidence: bool = False
    annotations: Dict[str, Any] = field(default_factory=dict)

    @property
    def contaminated(self) -> bool:
        return bool(self.contamination_findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "feature_signature": self.feature_signature,
            "status": self.status,
            "stability_score": round(self.stability_score, 3),
            "recurrence_count": self.recurrence_count,
            "source_distribution": dict(self.source_distribution),
            "modality_distribution": dict(self.modality_distribution),
            "supporting_event_ids": self.supporting_event_ids[:50],
            "contradicting_event_ids": self.contradicting_event_ids[:50],
            "contamination_findings": list(self.contamination_findings),
            "eligible": self.eligible,
            "is_counterevidence": self.is_counterevidence,
            "contaminated": self.contaminated,
            "annotations": dict(self.annotations),
            "annotations_are_ground_truth": False,
        }


@dataclass
class ConceptInputResult:
    """The aggregate concept-input loading result."""

    status: str = ConceptInputStatus.UNKNOWN
    concepts: List[LiveConceptInput] = field(default_factory=list)
    concept_memory_path: str = ""
    ontogenesis_report_present: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def eligible(self) -> List[LiveConceptInput]:
        return [c for c in self.concepts if c.eligible]

    @property
    def counterevidence(self) -> List[LiveConceptInput]:
        return [c for c in self.concepts if c.is_counterevidence]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_input_status": self.status,
            "concept_memory_path": self.concept_memory_path,
            "ontogenesis_report_present": self.ontogenesis_report_present,
            "live_eligible_concept_count": len(self.eligible),
            "counterevidence_concept_count": len(self.counterevidence),
            "contaminated_concept_count": sum(1 for c in self.concepts
                                              if c.contaminated),
            "concepts": [c.to_dict() for c in self.concepts],
            "notes": list(self.notes),
            "note": "only born/stable proto-concepts are eligible; contaminated "
                    "concepts are not eligible; rejected concepts remain visible "
                    "as counterevidence; labels/gloss are non-ground-truth "
                    "annotations only",
        }


@dataclass
class ConceptInputLoader:
    """Loads eligible proto-concepts + counterevidence from live ontogenesis."""

    def load(self, state_dir: str) -> ConceptInputResult:
        result = ConceptInputResult()
        onto = os.path.join(state_dir, "ontogenesis")
        report = os.path.join(onto, "reports", "LIVE_ONTOGENESIS_REPORT.json")
        result.ontogenesis_report_present = os.path.isfile(report)
        mem_path = os.path.join(onto, "concepts", "LIVE_CONCEPT_MEMORY.json")
        result.concept_memory_path = mem_path
        if not os.path.isfile(mem_path):
            result.status = ConceptInputStatus.MISSING_CONCEPT_MEMORY
            result.notes.append("live concept memory not found")
            return result
        try:
            with open(mem_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            result.status = ConceptInputStatus.MISSING_CONCEPT_MEMORY
            result.notes.append("live concept memory could not be read")
            return result
        for rec in data.get("records", []):
            result.concepts.append(self._concept_from_record(rec))
        result.status = (ConceptInputStatus.LOADED if result.eligible
                         else ConceptInputStatus.NO_ELIGIBLE_CONCEPTS)
        return result

    def from_records(self, records: List[Dict[str, Any]],
                     *, synthetic: bool = False) -> ConceptInputResult:
        """Build concept input directly from concept records (demo / synthetic)."""
        result = ConceptInputResult()
        for rec in records:
            result.concepts.append(self._concept_from_record(rec))
        if synthetic:
            result.status = ConceptInputStatus.SYNTHETIC
            result.notes.append("synthetic safe concepts (demo mode)")
        else:
            result.status = (ConceptInputStatus.LOADED if result.eligible
                             else ConceptInputStatus.NO_ELIGIBLE_CONCEPTS)
        return result

    @staticmethod
    def _concept_from_record(rec: Dict[str, Any]) -> LiveConceptInput:
        status = str(rec.get("status", "unknown"))
        contamination = list(rec.get("contamination_findings", []) or [])
        eligible = status in _ELIGIBLE_STATUSES and not contamination
        annotations: Dict[str, Any] = {}
        # Debug glosses / human labels may be carried as annotations only.
        if rec.get("debug_gloss_annotation"):
            annotations["debug_gloss"] = rec.get("debug_gloss_annotation")
        c = LiveConceptInput(
            concept_id=str(rec.get("concept_id", "")),
            feature_signature=str(rec.get("feature_signature", "")),
            status=status,
            stability_score=float(rec.get("stability_score", 0.0) or 0.0),
            recurrence_count=int(rec.get("recurrence_count", 0) or 0),
            source_distribution=dict(rec.get("source_distribution", {}) or {}),
            modality_distribution=dict(rec.get("modality_distribution", {})
                                       or {}),
            supporting_event_ids=list(rec.get("supporting_event_ids", []) or []),
            contradicting_event_ids=list(
                rec.get("contradicting_event_ids", []) or []),
            contamination_findings=contamination,
            eligible=eligible,
            is_counterevidence=status in _COUNTEREVIDENCE_STATUSES,
            annotations=annotations)
        return c
