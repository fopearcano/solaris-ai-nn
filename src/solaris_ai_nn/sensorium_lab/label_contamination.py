"""Human-label contamination -- labels are allowed, but must stay visible.

A :class:`HumanLabelContaminationAnalyzer` detects whether human annotations
quietly became ontology: human labels used as a primary category, an external
annotation treated as ground truth, text labels dominating proto-symbols, human
concepts dominating the world model, feature evidence ignored in favour of
labels, or a feeder annotation not marked external. Contamination is not always
bad, but it must never be silent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ContaminationSource:
    LABEL_AS_PRIMARY_CATEGORY = "human_object_label_as_primary_category"
    ANNOTATION_AS_GROUND_TRUTH = "external_annotation_treated_as_ground_truth"
    LABELS_DOMINATE_PROTO_SYMBOLS = "text_labels_dominate_proto_symbols"
    HUMAN_CONCEPTS_DOMINATE_WORLD = "human_concepts_dominate_world_model"
    FEATURE_EVIDENCE_IGNORED = "feature_evidence_ignored_for_labels"
    ANNOTATION_NOT_MARKED_EXTERNAL = "feeder_annotation_not_marked_external"

    ALL = (LABEL_AS_PRIMARY_CATEGORY, ANNOTATION_AS_GROUND_TRUTH,
           LABELS_DOMINATE_PROTO_SYMBOLS, HUMAN_CONCEPTS_DOMINATE_WORLD,
           FEATURE_EVIDENCE_IGNORED, ANNOTATION_NOT_MARKED_EXTERNAL)


@dataclass
class ContaminationReport:
    contamination_score: float
    sources: List[str] = field(default_factory=list)
    human_labelled_event_ratio: float = 0.0
    contaminated_symbol_count: int = 0
    notes: List[str] = field(default_factory=list)

    @property
    def contaminated(self) -> bool:
        return self.contamination_score > 0.0 or bool(self.sources)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contamination_score": self.contamination_score,
            "contaminated": self.contaminated,
            "sources": list(self.sources),
            "human_labelled_event_ratio": self.human_labelled_event_ratio,
            "contaminated_symbol_count": self.contaminated_symbol_count,
            "notes": list(self.notes),
            "note": "human labels are allowed as annotations; contamination is "
                    "reported, never silently turned into ontology",
        }


@dataclass
class HumanLabelContaminationAnalyzer:
    """Detects where human labels leaked into the internal structure."""

    def analyze(self, runtime: Any, *,
                human_labelled_events: int = 0,
                total_events: int = 0) -> ContaminationReport:
        if runtime is None:
            return ContaminationReport(contamination_score=0.0,
                                       notes=["no runtime; nothing analysed"])
        rt = runtime
        sources: List[str] = []

        contaminated_symbols = sum(
            1 for p in rt.proto_symbol_candidates
            if p.get("human_label_contaminated"))
        total_symbols = max(1, len(rt.proto_symbol_candidates))
        human_text_symbols = sum(
            1 for p in rt.proto_symbol_candidates
            if p.get("modality") == "human_textual")

        labelled_ratio = (human_labelled_events / total_events
                          if total_events else 0.0)

        grounding_score = rt.human_label_contamination_score()
        if contaminated_symbols:
            sources.append(ContaminationSource.LABELS_DOMINATE_PROTO_SYMBOLS)
        if grounding_score >= 0.5:
            sources.append(ContaminationSource.ANNOTATION_AS_GROUND_TRUTH)
        if total_symbols > 1 and human_text_symbols / total_symbols > 0.4:
            sources.append(ContaminationSource.LABEL_AS_PRIMARY_CATEGORY)
        if labelled_ratio >= 0.25:
            # External annotations are present in enough of the stream to have
            # shaped the structure; this is reported, not hidden.
            sources.append(ContaminationSource.HUMAN_CONCEPTS_DOMINATE_WORLD)
        if labelled_ratio > 0.5:
            sources.append(ContaminationSource.FEATURE_EVIDENCE_IGNORED)

        # Score blends the grounding-based score, the labelled-event ratio, and
        # the contaminated-symbol ratio.
        score = round(min(1.0, max(
            grounding_score, labelled_ratio,
            contaminated_symbols / total_symbols)), 4)
        notes: List[str] = []
        if score == 0.0:
            notes.append("no human-label contamination detected; grounding "
                         "rests on features")
        else:
            notes.append("human labels influenced the structure; this is "
                         "reported, not hidden")
        return ContaminationReport(
            contamination_score=score, sources=sources,
            human_labelled_event_ratio=round(labelled_ratio, 4),
            contaminated_symbol_count=contaminated_symbols, notes=notes)

    def validate_not_ground_truth(self, treated_as_truth: bool) -> bool:
        """Human labels can never be ground truth; returns False if attempted."""
        return not treated_as_truth
