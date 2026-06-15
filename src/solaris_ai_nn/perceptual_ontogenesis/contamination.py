"""Contamination analysis -- making human-label influence visible, not forbidden.

The :class:`ConceptContaminationAnalyzer` detects when a proto-concept is driven by
human labels rather than modality-native feature evidence. Human-labelled concepts
are NOT forbidden -- they must be *marked*, and contamination lowers grounding and
stability scores. Annotations are never treated as ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .proto_concepts import ProtoConcept, ProtoConceptGrounding, ProtoConceptKind


@dataclass
class ConceptContaminationReport:
    concept_id: str
    contamination_score: float
    flags: List[str] = field(default_factory=list)
    feature_grounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "contamination_score": round(self.contamination_score, 4),
            "flags": list(self.flags),
            "feature_grounded": self.feature_grounded,
            "note": "human-labelled concepts are allowed but marked; labels are "
                    "never ground truth",
        }


@dataclass
class ConceptContaminationAnalyzer:
    """Detects and scores human-label contamination in concept formation."""

    def analyze(self, concept: ProtoConcept) -> ConceptContaminationReport:
        flags: List[str] = []
        score = float(concept.human_label_contamination_score)

        if concept.kind == ProtoConceptKind.HUMAN_LABEL_CONTAMINATED:
            flags.append("concept_born_primarily_from_human_label")
            score = max(score, 0.8)
        if concept.grounding == ProtoConceptGrounding.LABEL_GROUNDED:
            flags.append("concept_grounded_in_label_not_feature")
            score = max(score, 0.6)
        if concept.human_annotations:
            flags.append("human_annotation_attached")
            # An annotation that is the *only* evidence is contamination.
            if concept.grounding_score < 0.2:
                flags.append("annotation_dominates_feature_evidence")
                score = max(score, 0.7)
        # Detect a human-text modality dominating the evidence.
        human_text = concept.modality_distribution.get("human_textual", 0)
        total = sum(concept.modality_distribution.values()) or 1
        if human_text / total >= 0.6:
            flags.append("human_text_modality_dominates")
            score = max(score, human_text / total)
        if concept.grounding_score < 0.1 and not concept.modality_distribution:
            flags.append("modality_native_features_ignored")
            score = max(score, 0.5)

        feature_grounded = score < 0.5
        # Contamination lowers grounding/stability (recorded on the concept).
        if score >= 0.5:
            concept.grounding_score = round(
                concept.grounding_score * (1.0 - 0.5 * score), 4)
            concept.stability_score = round(
                concept.stability_score * (1.0 - 0.5 * score), 4)
        concept.human_label_contamination_score = round(score, 4)
        return ConceptContaminationReport(
            concept_id=concept.concept_id, contamination_score=round(score, 4),
            flags=flags, feature_grounded=feature_grounded)

    def analyze_all(self, concepts: List[ProtoConcept],
                    ) -> List[ConceptContaminationReport]:
        return [self.analyze(c) for c in concepts]

    @staticmethod
    def contaminated_ratio(reports: List[ConceptContaminationReport]) -> float:
        if not reports:
            return 0.0
        n = sum(1 for r in reports if not r.feature_grounded)
        return round(n / len(reports), 4)
