"""Reviewer feedback assimilation runtime -- the bounded, offline assimilator.

:class:`ReviewerFeedbackAssimilationRuntime` loads local independent-review
artifacts and operator-provided reviewer feedback, classifies objections, ingests
reproduction outcomes, assesses claim and theory impact, builds an evidence gap
map, generates review-driven experiment recommendations and claim-revision
proposals, revises publication readiness, and maintains a review queue, then writes
reports. It reads local artifacts and writes local reports only: it publishes
nothing, uploads nothing, contacts no reviewer, calls no Git/GitHub or external
API, executes no reviewer command or experiment, runs no external agent, controls
no hardware/feeders/network/shell, and never trains on reviewer feedback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .claim_impact import ClaimImpactAssessor
from .claim_revision import ClaimRevisionProposer
from .evidence_gap_map import ReviewEvidenceGapMapBuilder
from .experiment_recommendations import ReviewDrivenExperimentRecommender
from .feedback_manifest import (
    FeedbackSourceType,
    ReviewerFeedbackArtifact,
    ReviewerFeedbackManifest,
)
from .objection_classifier import (
    ObjectionValidityStatus,
    ReviewerObjectionClassifier,
)
from .publication_readiness_revision import PublicationReadinessReviser
from .reproduction_outcomes import ReviewerReproductionOutcomeIngestor
from .review_queue import (
    ReviewAssimilationQueue,
    ReviewQueueItem,
    ReviewQueueItemType,
    ReviewQueuePriority,
)
from .safety import ReviewerFeedbackAssimilationSafetyValidator
from .theory_impact import TheoryImpactAssessor


@dataclass
class ReviewerFeedbackAssimilationRuntime:
    """Bounded, offline reviewer-feedback assimilation engine."""

    state_dir: str = ".solaris_ai_nn_review_assimilation"
    feedback_manifest_path: Optional[str] = None
    artifact_roots: List[str] = field(default_factory=list)
    max_objections: int = 200
    max_recommendations: int = 100
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_operator_review_for_claim_revision: bool = False
    require_safety_gate_pass: bool = True

    safety: ReviewerFeedbackAssimilationSafetyValidator = field(
        default_factory=ReviewerFeedbackAssimilationSafetyValidator, init=False)
    manifest: Any = field(default=None, init=False)
    objections: Dict[str, Any] = field(default_factory=dict, init=False)
    reproductions: Dict[str, Any] = field(default_factory=dict, init=False)
    claim_impact: Dict[str, Any] = field(default_factory=dict, init=False)
    theory_impact: Dict[str, Any] = field(default_factory=dict, init=False)
    evidence_gaps: Dict[str, Any] = field(default_factory=dict, init=False)
    recommendations: Dict[str, Any] = field(default_factory=dict, init=False)
    claim_revisions: Dict[str, Any] = field(default_factory=dict, init=False)
    publication_revision: Dict[str, Any] = field(default_factory=dict, init=False)
    queue: Any = field(default=None, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.manifest = ReviewerFeedbackManifest(state_dir=self.state_dir,
                                                 persist=not self.dry_run)
        self.queue = ReviewAssimilationQueue()
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        self._bundle = dict(bundle or {})

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bundle = self._bundle
        ir = bundle.get("independent_review", {}) or {}
        sci = bundle.get("scientific_claims", {}) or {}
        forbidden = sci.get("forbidden_claims", {}) or {}
        claim_registry = sci.get("claim_registry", {}) or {}
        claim_text_by_id = {c.get("claim_id", ""): c.get("text", "")
                            for c in claim_registry.get("claims", [])}

        # 1. Feedback manifest (index local feedback; missing stays visible).
        objection_records = self._gather_objections(bundle, ir)
        self._build_manifest(bundle, ir, objection_records)

        # 2. Objection classification.
        classifier = ReviewerObjectionClassifier()
        classifications = classifier.classify(
            objection_records, max_objections=self.max_objections)
        self.objections = ReviewerObjectionClassifier.summary(classifications)

        # 3. Reproduction outcomes.
        ingestor = ReviewerReproductionOutcomeIngestor()
        outcomes = ingestor.ingest(bundle.get("reproduction_outcomes", []))
        self.reproductions = ReviewerReproductionOutcomeIngestor.summary(outcomes)

        # 4. Claim impact.
        impacts = ClaimImpactAssessor().assess(
            objections=classifications, reproductions=outcomes)
        self.claim_impact = ClaimImpactAssessor.summary(impacts)

        # 5. Theory impact.
        theory_impacts = TheoryImpactAssessor().assess(
            objections=classifications,
            theory_links=bundle.get("theory_links", {}))
        self.theory_impact = TheoryImpactAssessor.summary(theory_impacts)

        # 6. Evidence gap map.
        gap_map = ReviewEvidenceGapMapBuilder().build(
            objections=classifications, reproductions=outcomes,
            missing_artifacts=bundle.get("missing_artifacts", []))
        self.evidence_gaps = gap_map.to_dict()

        # 7. Experiment recommendations.
        recs = ReviewDrivenExperimentRecommender().recommend(
            objections=classifications, gaps=gap_map.gaps,
            max_recommendations=self.max_recommendations)
        self.recommendations = ReviewDrivenExperimentRecommender.summary(recs)

        # 8. Claim revision proposals (proposal-only).
        proposals = ClaimRevisionProposer(
            require_operator_review=self.require_operator_review_for_claim_revision
        ).propose(impacts=impacts, claim_text_by_id=claim_text_by_id)
        self.claim_revisions = ClaimRevisionProposer.summary(proposals)

        # 9. Publication readiness revision.
        forbidden_asserted = forbidden.get("asserted_forbidden_count", 0) > 0 \
            or self.claim_impact.get("claim_forbidden_count", 0) > 0
        self.publication_revision = PublicationReadinessReviser().revise(
            objection_summary=self.objections,
            claim_impact_summary=self.claim_impact,
            reproduction_summary=self.reproductions,
            evidence_gap_map=self.evidence_gaps,
            forbidden_asserted=forbidden_asserted,
            safety_boundary_present=self._has_safety_boundary(bundle)).to_dict()

        # 10. Review queue.
        self._build_queue(classifications, gap_map, recs, proposals)

        return {"refused": False,
                "objection_count": self.objections["reviewer_objection_count"],
                "publication_readiness_impact":
                    self.publication_revision["publication_readiness_impact"]}

    # -- helpers ------------------------------------------------------------

    def _gather_objections(self, bundle: Dict[str, Any],
                           ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge operator-provided objections with response-ledger objections."""
        out: List[Dict[str, Any]] = list(bundle.get("objections", []) or [])
        seen = {o.get("objection_id") for o in out}
        ledger = ir.get("response_ledger", {}) or {}
        for o in ledger.get("objections", []) or []:
            oid = o.get("objection_id")
            if oid in seen:
                continue
            # Map a response-ledger status onto a validity heuristic.
            status = o.get("status", "")
            validity = {
                "accepted_as_limitation":
                    ObjectionValidityStatus.ACCEPTED_AS_LIMITATION,
                "accepted_as_falsification":
                    ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION,
                "rejected_with_evidence":
                    ObjectionValidityStatus.INVALID_WITH_EVIDENCE,
                "unresolved": ObjectionValidityStatus.UNRESOLVED,
            }.get(status, ObjectionValidityStatus.UNRESOLVED)
            out.append({"objection_id": oid, "text": o.get("text", ""),
                        "validity": validity,
                        "claim_refs": o.get("claim_refs", [])})
        return out

    def _build_manifest(self, bundle: Dict[str, Any], ir: Dict[str, Any],
                        objection_records: List[Dict]) -> None:
        for o in objection_records:
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=FeedbackSourceType.REVIEWER_OBJECTION,
                ref=str(o.get("objection_id", "")),
                summary=str(o.get("text", ""))[:80]))
        if ir.get("adversarial_findings"):
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=FeedbackSourceType.ADVERSARIAL_REVIEW_FINDING,
                ref="adversarial_findings",
                summary="adversarial alternative explanations"))
        else:
            self.manifest.add_missing(
                FeedbackSourceType.ADVERSARIAL_REVIEW_FINDING)
        if ir.get("audit_matrix"):
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=FeedbackSourceType.AUDIT_MATRIX_BLOCKER,
                ref="audit_matrix", summary="audit matrix blockers"))
        if ir.get("response_ledger"):
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=FeedbackSourceType.RESPONSE_LEDGER_ENTRY,
                ref="response_ledger", summary="reviewer response ledger"))
        else:
            self.manifest.add_missing(FeedbackSourceType.RESPONSE_LEDGER_ENTRY)
        for r in bundle.get("reproduction_outcomes", []) or []:
            src = (FeedbackSourceType.SUCCESSFUL_REPRODUCTION
                   if r.get("status") in ("reproduced", "partially_reproduced")
                   else FeedbackSourceType.FAILED_REPRODUCTION)
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=src, ref=str(r.get("challenge_type", "")),
                summary=str(r.get("status", ""))))
        for note in bundle.get("reviewer_notes", []) or []:
            self.manifest.add(ReviewerFeedbackArtifact(
                source_type=FeedbackSourceType.OPERATOR_NOTE,
                summary=str(note)[:80]))
        if not self.dry_run:
            self.manifest.persist_manifest()

    def _build_queue(self, classifications, gap_map, recs, proposals) -> None:
        for c in classifications:
            if c.open:
                self.queue.add(ReviewQueueItem(
                    item_type=ReviewQueueItemType.ARCHIVE_UNRESOLVED_OBJECTION
                    if not c.critical
                    else ReviewQueueItemType.REQUEST_OPERATOR_DECISION,
                    priority=(ReviewQueuePriority.URGENT if c.critical
                              else ReviewQueuePriority.MEDIUM),
                    status="unresolved", refs=[c.objection_id],
                    detail=f"open objection {c.category}"))
        for g in gap_map.gaps:
            self.queue.add(ReviewQueueItem(
                item_type=ReviewQueueItemType.COLLECT_MISSING_ARTIFACT,
                priority=(ReviewQueuePriority.URGENT if g.blocks_readiness
                          else ReviewQueuePriority.HIGH),
                refs=list(g.claim_refs), detail=f"evidence gap {g.category}"))
        for p in proposals:
            self.queue.add(ReviewQueueItem(
                item_type=ReviewQueueItemType.UPDATE_CLAIM_REGISTRY,
                priority=ReviewQueuePriority.HIGH, refs=[p.claim_id],
                detail=f"claim revision proposal {p.revision_type}"))
        if self.recommendations.get("reviewer_driven_experiment_count", 0):
            self.queue.add(ReviewQueueItem(
                item_type=ReviewQueueItemType.RERUN_REPRODUCTION_CHALLENGE,
                priority=ReviewQueuePriority.HIGH,
                detail="reviewer-driven experiments recommended"))

    @staticmethod
    def _has_safety_boundary(bundle: Dict[str, Any]) -> bool:
        ir = bundle.get("independent_review", {}) or {}
        sci = bundle.get("scientific_claims", {}) or {}
        return bool(bundle.get("safety")
                    or ir.get("review_readiness")
                    or sci.get("limitations"))

    # -- integration views --------------------------------------------------

    def review_assimilation_status(self) -> Dict[str, Any]:
        m = self.manifest.index()
        return {
            "review_assimilation_enabled": True,
            "reviewer_feedback_artifact_count": m[
                "reviewer_feedback_artifact_count"],
            "reviewer_objection_count": self.objections.get(
                "reviewer_objection_count", 0),
            "valid_objection_count": self.objections.get(
                "valid_objection_count", 0),
            "partially_valid_objection_count": self.objections.get(
                "partially_valid_objection_count", 0),
            "unresolved_objection_count": self.objections.get(
                "unresolved_objection_count", 0),
            "critical_objection_count": self.objections.get(
                "critical_objection_count", 0),
            "unresolved_critical_objection_count": self.objections.get(
                "critical_unresolved_count", 0),
            "reproduction_outcome_count": self.reproductions.get(
                "reproduction_outcome_count", 0),
            "reproduction_success_count": self.reproductions.get(
                "reproduction_success_count", 0),
            "reproduction_failure_count": self.reproductions.get(
                "reproduction_failure_count", 0),
            "claim_impact_count": self.claim_impact.get("claim_impact_count", 0),
            "claim_downgrade_count": self.claim_impact.get(
                "claim_downgrade_count", 0),
            "claim_falsification_count": self.claim_impact.get(
                "claim_falsification_count", 0),
            "theory_impact_count": self.theory_impact.get(
                "theory_impact_count", 0),
            "theory_revision_count": self.theory_impact.get(
                "theory_revision_count", 0),
            "evidence_gap_count": self.evidence_gaps.get("evidence_gap_count", 0),
            "critical_evidence_gap_count": self.evidence_gaps.get(
                "critical_evidence_gap_count", 0),
            "reviewer_driven_experiment_count": self.recommendations.get(
                "reviewer_driven_experiment_count", 0),
            "claim_revision_proposal_count": self.claim_revisions.get(
                "claim_revision_proposal_count", 0),
            "publication_readiness_impact": self.publication_revision.get(
                "publication_readiness_impact"),
            "publication_readiness_blocker_count": self.publication_revision.get(
                "publication_readiness_blocker_count", 0),
            "review_queue_item_count": self.queue.to_dict()[
                "review_queue_item_count"],
            "review_assimilation_safety_block_count": self.safety.rejected_count,
            "latest_review_assimilation_report_path": self._report_path(),
            "trains_model": False, "published": False, "uploaded": False,
            "contacted_reviewers": False, "runs_git": False,
            "calls_github": False,
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "REVIEW_ASSIMILATION_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.review_assimilation_status()

    # -- structured downstream outputs --------------------------------------

    def scientific_claims_proposals(self) -> Dict[str, Any]:
        """Structured proposals for the Scientific Claims layer."""
        return {
            "claim_impacts": self.claim_impact.get("impacts", []),
            "claim_revision_proposals": self.claim_revisions.get("proposals", []),
            "publication_readiness_revision": self.publication_revision,
            "forbidden_claim_risk":
                self.claim_impact.get("claim_forbidden_count", 0) > 0,
        }

    def architecture_compiler_inputs(self) -> List[Dict[str, Any]]:
        """Experiment recommendations suitable for Architecture / Compiler."""
        return [r for r in self.recommendations.get("recommendations", [])
                if r.get("is_experiment_input")]

    def research_cycle_inputs(self) -> Dict[str, Any]:
        """Evidence gaps + queue + unresolved critical objections for the cycle."""
        return {
            "evidence_gaps": self.evidence_gaps.get("gaps", []),
            "review_queue": self.queue.to_dict()["items"],
            "unresolved_critical_objection_count": self.objections.get(
                "critical_unresolved_count", 0),
            "publication_blocked":
                self.publication_revision.get("publication_readiness_impact")
                == "block_publication",
        }

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ReviewerFeedbackAssimilationReportBuilder

        return ReviewerFeedbackAssimilationReportBuilder(self).write()
