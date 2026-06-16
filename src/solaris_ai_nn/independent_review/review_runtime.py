"""Independent review runtime -- the bounded, offline review-prep engine.

:class:`IndependentReviewRuntime` loads the prior-layer artifacts (scientific
claims, research baseline, research cycle, soak/replication/falsification, safety/
evaluation), builds the review manifest, runs sanitizer checks, builds the reviewer
pack, reproducibility challenges, review protocol, reviewer questions, adversarial
review, audit matrix, response ledger, and evaluates review readiness, then writes
review documents. It reads local artifacts and writes review documents only: it
publishes nothing, uploads nothing, calls no Git/GitHub or external API, runs no
experiment or command, runs no external agent, and controls no feeders/hardware/
network/shell.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .adversarial_review import AdversarialReviewEngine
from .artifact_sanitizer import ReviewArtifactSanitizer
from .audit_matrix import IndependentReviewAuditMatrix
from .response_ledger import ReviewerResponseLedger, load_objections
from .review_manifest import (
    ARTIFACT_CATEGORIES,
    IndependentReviewManifest,
    ReviewArtifact,
    ReviewArtifactStatus,
    ReviewScope,
)
from .review_protocol import IndependentReviewProtocol
from .review_readiness import IndependentReviewReadinessEvaluator
from .reviewer_pack import ReviewerPackBuilder
from .reviewer_questions import ReviewerQuestionGenerator
from .reproducibility_challenge import ReproducibilityChallengeBuilder
from .safety import IndependentReviewSafetyValidator

# bundle key -> review artifact category for manifest indexing.
_ARTIFACT_MAP = (
    ("research_baseline", "research_baseline_report"),
    ("reproducibility_bundle", "reproducibility_bundle"),
    ("scientific_claims", "scientific_claim_report"),
    ("publication_dossier", "publication_dossier"),
    ("safe_abstracts", "safe_abstracts"),
    ("claim_registry", "claim_registry"),
    ("theory_ledger", "theory_ledger"),
    ("evidence_map", "evidence_map"),
    ("counterevidence", "counterevidence_report"),
    ("limitations", "limitations_report"),
    ("soak", "soak_dossier"),
    ("replication", "replication_report"),
    ("falsification", "falsification_report"),
    ("research_cycle", "research_cycle_report"),
    ("architecture_evolution", "architecture_evolution_report"),
    ("implementation_intake", "implementation_intake_report"),
    ("post_merge", "post_merge_assimilation_report"),
    ("safety", "safety_invariant_report"),
    ("evaluation", "evaluation_report"),
    ("fixtures", "fixture_data"),
    ("synthetic_examples", "synthetic_examples"),
    ("operator_notes", "operator_notes"),
)


@dataclass
class IndependentReviewRuntime:
    """Bounded, offline independent-review preparation engine."""

    state_dir: str = ".solaris_ai_nn_review"
    artifact_roots: List[str] = field(default_factory=list)
    objection_file: Optional[str] = None
    max_questions: int = 50
    max_challenges: int = 50
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_sanitizer_pass: bool = True
    require_claimguard_pass: bool = True
    publication_review_mode: str = "internal"

    safety: IndependentReviewSafetyValidator = field(
        default_factory=IndependentReviewSafetyValidator, init=False)
    manifest: Any = field(default=None, init=False)
    sanitizer_report: Dict[str, Any] = field(default_factory=dict, init=False)
    reviewer_pack: Dict[str, Any] = field(default_factory=dict, init=False)
    challenges: Dict[str, Any] = field(default_factory=dict, init=False)
    protocol: Dict[str, Any] = field(default_factory=dict, init=False)
    questions: Dict[str, Any] = field(default_factory=dict, init=False)
    adversarial: Dict[str, Any] = field(default_factory=dict, init=False)
    audit_matrix: Dict[str, Any] = field(default_factory=dict, init=False)
    ledger: Any = field(default=None, init=False)
    readiness: Dict[str, Any] = field(default_factory=dict, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        scope = {"internal": ReviewScope.INTERNAL,
                 "friendly": ReviewScope.FRIENDLY_EXTERNAL,
                 "hostile": ReviewScope.HOSTILE_EXTERNAL}.get(
                     self.publication_review_mode, ReviewScope.INTERNAL)
        self.manifest = IndependentReviewManifest(
            state_dir=self.state_dir, scope=scope, persist=not self.dry_run)
        self.ledger = ReviewerResponseLedger(state_dir=self.state_dir,
                                             persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        self._bundle = dict(bundle or {})

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bundle = self._bundle
        sci = bundle.get("scientific_claims", {}) or {}
        claim_registry = sci.get("claim_registry", {}) or {}
        counterevidence = sci.get("counterevidence", {}) or {}
        forbidden = sci.get("forbidden_claims", {}) or {}
        limitations = sci.get("limitations", {}) or {}
        claims = claim_registry.get("claims", [])

        # 1. Review manifest (index local artifacts; missing stay visible).
        self._build_manifest(bundle, sci, claims)

        # 2. Sanitizer (scan local text artifacts; read-only).
        sanitizer = ReviewArtifactSanitizer().scan_artifacts(
            self._sanitizer_inputs(bundle),
            has_license_readme=bool(bundle.get("has_license_readme", True)))
        self.sanitizer_report = sanitizer.to_dict()

        # 3. Reproducibility challenges (instructions only).
        challenge = ReproducibilityChallengeBuilder().build(
            bundle, max_challenges=self.max_challenges)
        self.challenges = challenge.to_dict()

        # 4. Review protocol (advisory).
        self.protocol = IndependentReviewProtocol().to_dict()

        # 5. Reviewer questions (hostile but useful).
        questions = ReviewerQuestionGenerator().generate(
            claims=claims, max_questions=self.max_questions)
        self.questions = ReviewerQuestionGenerator.summary(questions)

        # 6. Adversarial review (alternatives preserved).
        adv_bundle = dict(bundle)
        adv_bundle["counterevidence"] = counterevidence
        self.adversarial = AdversarialReviewEngine().review(adv_bundle).to_dict()

        # 7. Audit matrix (gaps visible).
        q_by_cat = {}
        for q in questions:
            q_by_cat.setdefault(q.category, q.text)
        self.audit_matrix = IndependentReviewAuditMatrix().build(
            claims=claims, counterevidence=counterevidence,
            limitations=limitations,
            question_by_category=q_by_cat).to_dict()

        # 8. Response ledger (operator-provided objections only).
        for objection in load_objections(bundle.get("objections")):
            self.ledger.add_objection(objection)

        # 9. Reviewer pack (claim-constrained).
        self.reviewer_pack = ReviewerPackBuilder().build(
            claim_registry=claim_registry, counterevidence=counterevidence,
            limitations=limitations, manifest=self.manifest.to_dict(),
            challenges=self.challenges, questions=self.questions,
            baseline_status=str((bundle.get("research_baseline", {}) or {}).get(
                "baseline_status", "")),
            safety_boundary=self._safety_boundary(bundle),
            sanitizer_blocked=sanitizer.blocks_readiness).to_dict()

        # 10. Review readiness (advisory; inspectability, not claim strength).
        self.readiness = IndependentReviewReadinessEvaluator().evaluate(
            manifest=self.manifest.index(), sanitizer=self.sanitizer_report,
            claim_registry=claim_registry, forbidden=forbidden,
            adversarial=self.adversarial, audit_matrix=self.audit_matrix,
            response_ledger=self.ledger.to_dict(), challenges=self.challenges,
            safety_boundary_present=self._has_safety_boundary(bundle)).to_dict()

        if not self.dry_run:
            self.manifest.persist_manifest()
        return {"refused": False,
                "readiness": self.readiness.get("review_readiness_status"),
                "artifact_count":
                    self.manifest.index()["independent_review_artifact_count"]}

    # -- helpers ------------------------------------------------------------

    def _build_manifest(self, bundle: Dict[str, Any], sci: Dict[str, Any],
                        claims: List[Dict]) -> None:
        falsified_present = any(
            c.get("status") in ("falsified", "contradicted", "unsupported")
            for c in claims)
        # Claim-layer sub-artifacts are nested under scientific_claims.
        for key, category in _ARTIFACT_MAP:
            present = bool(bundle.get(key)) or bool(sci.get(key))
            if present:
                self.manifest.add(ReviewArtifact(
                    category=category, ref=key,
                    status=ReviewArtifactStatus.PRESENT,
                    is_negative_or_falsified=(
                        category in ("falsification_report",
                                     "counterevidence_report")
                        or (category == "claim_registry" and falsified_present))))
            else:
                self.manifest.add_missing(category)

    def _sanitizer_inputs(self, bundle: Dict[str, Any]) -> Dict[str, str]:
        """Collect local text the sanitizer should scan."""
        out: Dict[str, str] = {}
        for key, text in (bundle.get("sanitizer_inputs", {}) or {}).items():
            out[str(key)] = str(text)
        # Also scan operator notes if provided as text.
        notes = bundle.get("operator_notes")
        if isinstance(notes, str):
            out["operator_notes"] = notes
        return out

    @staticmethod
    def _has_safety_boundary(bundle: Dict[str, Any]) -> bool:
        rb = bundle.get("research_baseline", {}) or {}
        return bool(bundle.get("safety")
                    or rb.get("safety_boundary_status"))

    def _safety_boundary(self, bundle: Dict[str, Any]) -> str:
        rb = bundle.get("research_baseline", {}) or {}
        status = rb.get("safety_boundary_status")
        if status:
            return (f"safety boundary status: {status}; no actuation, hardware, "
                    "feeders, network, shell, or Git/GitHub automation")
        return ("no actuation, no hardware/feeder/network/shell, no source "
                "self-rewrite, no Git/GitHub automation")

    # -- integration views --------------------------------------------------

    def independent_review_status(self) -> Dict[str, Any]:
        m = self.manifest.index()
        return {
            "independent_review_enabled": True,
            "independent_review_artifact_count": m[
                "independent_review_artifact_count"],
            "missing_review_artifact_count": m["missing_review_artifact_count"],
            "missing_critical_artifact_count": m[
                "missing_critical_artifact_count"],
            "sanitizer_finding_count": self.sanitizer_report.get(
                "sanitizer_finding_count", 0),
            "critical_sanitizer_finding_count": self.sanitizer_report.get(
                "critical_sanitizer_finding_count", 0),
            "reproducibility_challenge_count": self.challenges.get(
                "reproducibility_challenge_count", 0),
            "unavailable_challenge_count": self.challenges.get(
                "unavailable_challenge_count", 0),
            "reviewer_question_count": self.questions.get(
                "reviewer_question_count", 0),
            "adversarial_finding_count": self.adversarial.get(
                "adversarial_finding_count", 0),
            "alternative_explanation_count": self.adversarial.get(
                "alternative_explanation_count", 0),
            "audit_matrix_blocker_count": self.audit_matrix.get(
                "audit_matrix_blocker_count", 0),
            "unresolved_objection_count": self.ledger.to_dict()[
                "unresolved_objection_count"],
            "review_readiness_status": self.readiness.get(
                "review_readiness_status"),
            "review_readiness_blocker_count": self.readiness.get(
                "review_readiness_blocker_count", 0),
            "independent_review_safety_block_count": self.safety.rejected_count,
            "latest_independent_review_report_path": self._report_path(),
            "published": False, "uploaded": False, "contacted_reviewers": False,
            "runs_git": False, "calls_github": False,
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "INDEPENDENT_REVIEW_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.independent_review_status()

    def experiment_inputs(self) -> List[Dict[str, str]]:
        """Unresolved objections + strong alternatives -> future experiment inputs."""
        out: List[Dict[str, str]] = []
        for o in self.ledger.unresolved_objections():
            out.append({"source": "unresolved_objection",
                        "experiment_input": o.text})
        for e in self.adversarial.get("explanations", []):
            if e.get("strong"):
                out.append({"source": "adversarial_alternative",
                            "experiment_input": e.get("evidence_needed", "")})
        return out

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import IndependentReviewReportBuilder

        return IndependentReviewReportBuilder(self).write()
