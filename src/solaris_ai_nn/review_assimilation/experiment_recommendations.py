"""Review-driven experiment recommendations -- instructions, never executed.

:class:`ReviewDrivenExperimentRecommender` turns evidence gaps and objections into
recommended experiments/tasks (reproductions, fixtures, control arms, ablations,
shuffled-order/random-label controls, live comparison, longer soak, replication,
falsification, metric/documentation improvements, claim/theory/dossier revisions,
public-claim blocks). Recommendations are instructions only -- no experiment is
executed and no branch is created -- high-risk ones carry safety context, and they
are suitable as inputs to Architecture Evolution or the Experiment Compiler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .evidence_gap_map import EvidenceGapCategory
from .objection_classifier import ObjectionCategory


class RecommendationType:
    RUN_MISSING_REPRODUCTION = "run_missing_reproduction"
    ADD_FIXTURE = "add_fixture"
    ADD_CONTROL_ARM = "add_control_arm"
    RUN_PASSIVE_PARSER_CONTROL = "run_passive_parser_control"
    RUN_NO_METABOLISM_ABLATION = "run_no_metabolism_ablation"
    RUN_NO_SEMIOGENESIS_ABLATION = "run_no_semiogenesis_ablation"
    RUN_SHUFFLED_EVENT_ORDER = "run_shuffled_event_order"
    RUN_RANDOM_LABEL_CONTROL = "run_random_label_control"
    RUN_LIVE_READ_ONLY_COMPARISON = "run_live_read_only_comparison"
    RUN_LONGER_SOAK = "run_longer_soak"
    RUN_REPLICATION = "run_replication"
    RUN_FALSIFICATION = "run_falsification"
    IMPROVE_METRIC_DEFINITION = "improve_metric_definition"
    IMPROVE_ARTIFACT_DOCUMENTATION = "improve_artifact_documentation"
    REVISE_CLAIM = "revise_claim"
    REVISE_THEORY = "revise_theory"
    REVISE_PUBLICATION_DOSSIER = "revise_publication_dossier"
    BLOCK_PUBLIC_CLAIM = "block_public_claim"
    UNKNOWN = "unknown"

    ALL = (RUN_MISSING_REPRODUCTION, ADD_FIXTURE, ADD_CONTROL_ARM,
           RUN_PASSIVE_PARSER_CONTROL, RUN_NO_METABOLISM_ABLATION,
           RUN_NO_SEMIOGENESIS_ABLATION, RUN_SHUFFLED_EVENT_ORDER,
           RUN_RANDOM_LABEL_CONTROL, RUN_LIVE_READ_ONLY_COMPARISON,
           RUN_LONGER_SOAK, RUN_REPLICATION, RUN_FALSIFICATION,
           IMPROVE_METRIC_DEFINITION, IMPROVE_ARTIFACT_DOCUMENTATION,
           REVISE_CLAIM, REVISE_THEORY, REVISE_PUBLICATION_DOSSIER,
           BLOCK_PUBLIC_CLAIM, UNKNOWN)

    # Recommendations that need explicit safety context for the operator.
    HIGH_RISK = (RUN_LIVE_READ_ONLY_COMPARISON, BLOCK_PUBLIC_CLAIM)
    # Recommendations suitable as Experiment Compiler / Architecture inputs.
    EXPERIMENT_INPUTS = (RUN_MISSING_REPRODUCTION, ADD_CONTROL_ARM,
                         RUN_PASSIVE_PARSER_CONTROL, RUN_NO_METABOLISM_ABLATION,
                         RUN_NO_SEMIOGENESIS_ABLATION, RUN_SHUFFLED_EVENT_ORDER,
                         RUN_RANDOM_LABEL_CONTROL, RUN_LIVE_READ_ONLY_COMPARISON,
                         RUN_LONGER_SOAK, RUN_REPLICATION, RUN_FALSIFICATION)


class RecommendationPriority:
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    ALL = (URGENT, HIGH, MEDIUM, LOW)


# objection category -> recommendation type.
_CATEGORY_REC = {
    ObjectionCategory.FAILED_REPRODUCTION:
        RecommendationType.RUN_MISSING_REPRODUCTION,
    ObjectionCategory.FIXTURE_OVERFIT:
        RecommendationType.RUN_LIVE_READ_ONLY_COMPARISON,
    ObjectionCategory.HUMAN_LABEL_CONTAMINATION:
        RecommendationType.RUN_RANDOM_LABEL_CONTROL,
    ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE:
        RecommendationType.RUN_PASSIVE_PARSER_CONTROL,
    ObjectionCategory.LOG_ACCUMULATION_ALTERNATIVE:
        RecommendationType.RUN_SHUFFLED_EVENT_ORDER,
    ObjectionCategory.INSUFFICIENT_CONTROLS: RecommendationType.ADD_CONTROL_ARM,
    ObjectionCategory.INSUFFICIENT_REPLICATION:
        RecommendationType.RUN_REPLICATION,
    ObjectionCategory.MISSING_EVIDENCE:
        RecommendationType.IMPROVE_ARTIFACT_DOCUMENTATION,
    ObjectionCategory.UNCLEAR_METRIC: RecommendationType.IMPROVE_METRIC_DEFINITION,
    ObjectionCategory.UNCLEAR_METHOD:
        RecommendationType.IMPROVE_ARTIFACT_DOCUMENTATION,
    ObjectionCategory.DOCUMENTATION_CONCERN:
        RecommendationType.IMPROVE_ARTIFACT_DOCUMENTATION,
    ObjectionCategory.UNSUPPORTED_CLAIM: RecommendationType.REVISE_CLAIM,
    ObjectionCategory.FORBIDDEN_CLAIM_RISK: RecommendationType.BLOCK_PUBLIC_CLAIM,
    ObjectionCategory.WEAK_EVIDENCE: RecommendationType.RUN_REPLICATION,
    ObjectionCategory.STATISTICAL_CONCERN: RecommendationType.RUN_REPLICATION,
    ObjectionCategory.INTERPRETATION_CONCERN: RecommendationType.REVISE_CLAIM,
    ObjectionCategory.BASELINE_CONCERN: RecommendationType.ADD_CONTROL_ARM,
}
# evidence gap category -> recommendation type.
_GAP_REC = {
    EvidenceGapCategory.MISSING_FIXTURE: RecommendationType.ADD_FIXTURE,
    EvidenceGapCategory.MISSING_CONTROL: RecommendationType.ADD_CONTROL_ARM,
    EvidenceGapCategory.MISSING_REPLICATION: RecommendationType.RUN_REPLICATION,
    EvidenceGapCategory.MISSING_FALSIFICATION:
        RecommendationType.RUN_FALSIFICATION,
    EvidenceGapCategory.MISSING_LIVE_DATA:
        RecommendationType.RUN_LIVE_READ_ONLY_COMPARISON,
    EvidenceGapCategory.MISSING_METRIC_DEFINITION:
        RecommendationType.IMPROVE_METRIC_DEFINITION,
    EvidenceGapCategory.MISSING_COMMAND:
        RecommendationType.IMPROVE_ARTIFACT_DOCUMENTATION,
    EvidenceGapCategory.MISSING_ARTIFACT:
        RecommendationType.IMPROVE_ARTIFACT_DOCUMENTATION,
}


@dataclass
class ReviewDrivenExperimentRecommendation:
    """One review-driven recommendation (instruction only; never executed)."""

    recommendation_type: str
    priority: str = RecommendationPriority.MEDIUM
    claim_refs: List[str] = field(default_factory=list)
    safety_context: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.recommendation_type not in RecommendationType.ALL:
            self.recommendation_type = RecommendationType.UNKNOWN
        if self.recommendation_type in RecommendationType.HIGH_RISK \
                and not self.safety_context:
            self.safety_context = ("operator review + safety gates required "
                                   "before acting; nothing is executed here")

    @property
    def is_experiment_input(self) -> bool:
        return self.recommendation_type in RecommendationType.EXPERIMENT_INPUTS

    def to_dict(self) -> Dict[str, Any]:
        return {"recommendation_type": self.recommendation_type,
                "priority": self.priority, "claim_refs": list(self.claim_refs),
                "safety_context": self.safety_context, "detail": self.detail,
                "is_experiment_input": self.is_experiment_input,
                "executed": False, "creates_branch": False}


@dataclass
class ReviewDrivenExperimentRecommender:
    """Generates review-driven recommendations (instructions only)."""

    def recommend(self, *, objections: List[Any], gaps: List[Any],
                  max_recommendations: int = 100,
                  ) -> List[ReviewDrivenExperimentRecommendation]:
        out: List[ReviewDrivenExperimentRecommendation] = []
        seen = set()

        def add(rtype: str, *, priority: str, claim_refs=None, detail=""):
            key = (rtype, tuple(claim_refs or []))
            if key in seen:
                return
            seen.add(key)
            out.append(ReviewDrivenExperimentRecommendation(
                recommendation_type=rtype, priority=priority,
                claim_refs=list(claim_refs or []), detail=detail))

        for c in objections:
            rtype = _CATEGORY_REC.get(c.category)
            if rtype is None:
                continue
            priority = (RecommendationPriority.URGENT if c.critical
                        else RecommendationPriority.HIGH if c.severity == "major"
                        else RecommendationPriority.MEDIUM)
            add(rtype, priority=priority, claim_refs=c.claim_refs,
                detail=f"addresses objection {c.objection_id} ({c.category})")
        for g in gaps:
            rtype = _GAP_REC.get(g.category)
            if rtype is None:
                continue
            priority = (RecommendationPriority.URGENT if g.blocks_readiness
                        else RecommendationPriority.HIGH)
            add(rtype, priority=priority, claim_refs=g.claim_refs,
                detail=f"closes evidence gap {g.category}")
        return out[:max_recommendations]

    @staticmethod
    def summary(recs: List[ReviewDrivenExperimentRecommendation],
                ) -> Dict[str, Any]:
        return {
            "reviewer_driven_experiment_count": len(recs),
            "experiment_input_count": sum(1 for r in recs
                                          if r.is_experiment_input),
            "high_risk_count": sum(1 for r in recs if r.safety_context),
            "recommendations": [r.to_dict() for r in recs],
            "note": "recommendations are instructions only; no experiment is "
                    "executed and no branch is created; high-risk ones carry "
                    "safety context and they suit Architecture Evolution / "
                    "Experiment Compiler inputs",
        }
