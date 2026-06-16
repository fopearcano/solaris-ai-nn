"""Scientific claim runtime -- the bounded, read-only claim-discipline engine.

:class:`ScientificClaimRuntime` loads the evidence from the prior layers (research
cycle, research baseline, soak/replication/falsification, module reports, safety/
evaluation), builds the evidence map and claim registry, updates the theory
ledger, detects counterevidence and forbidden claims, evaluates claim strength,
builds limitations, assembles a draft publication dossier and safe abstracts, runs
the ClaimGuard bridge, and writes reports. It reads evidence and writes reports
only: it modifies no source, runs no Git, calls no GitHub, runs no experiment,
executes no validation, runs no external agent, controls no feeders/hardware/
network/shell, creates no release, and makes no consciousness/life/agency claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .abstract_builder import AbstractVariant, ScientificAbstractBuilder
from .claim_guard_bridge import ClaimGuardBridge
from .claim_registry import (
    ClaimCategory,
    ClaimRegistry,
    ClaimStatus,
    ScientificClaim,
)
from .claim_strength import ClaimStrength, ClaimStrengthEvaluator
from .counterevidence import CounterEvidenceAnalyzer
from .evidence_mapping import EvidenceMap, EvidenceRole, MappedEvidence
from .forbidden_claims import ForbiddenClaimDetector
from .limitations_builder import LimitationsBuilder
from .publication_dossier import (
    PublicationDossierBuilder,
    PublicationReadinessStatus,
)
from .safety import ScientificClaimSafetyValidator
from .theory_ledger import TheoryLedger, TheoryStatement, TheoryStatus


@dataclass
class ScientificClaimRuntime:
    """Bounded, read-only scientific claim-discipline engine."""

    state_dir: str = ".solaris_ai_nn_claims"
    artifact_roots: List[str] = field(default_factory=list)
    max_claims: int = 200
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_replication_for_strong_claim: bool = True
    require_falsification_for_publishable_claim: bool = False
    require_claimguard: bool = True
    publication_mode: str = "internal_report"

    safety: ScientificClaimSafetyValidator = field(
        default_factory=ScientificClaimSafetyValidator, init=False)
    registry: Any = field(default=None, init=False)
    theory: Any = field(default_factory=TheoryLedger, init=False)
    evidence_map: Any = field(default_factory=EvidenceMap, init=False)
    counterevidence: Dict[str, Any] = field(default_factory=dict, init=False)
    forbidden: Dict[str, Any] = field(default_factory=dict, init=False)
    limitations: Dict[str, Any] = field(default_factory=dict, init=False)
    dossier: Dict[str, Any] = field(default_factory=dict, init=False)
    abstracts: Dict[str, str] = field(default_factory=dict, init=False)
    claim_guard: Any = field(default=None, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.registry = ClaimRegistry(state_dir=self.state_dir,
                                      persist=not self.dry_run)
        self.claim_guard = ClaimGuardBridge(
            require_claimguard=self.require_claimguard)
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        self._bundle = dict(bundle or {})

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bundle = self._bundle
        detector = ForbiddenClaimDetector()
        evaluator = ClaimStrengthEvaluator(
            require_replication_for_strong=self.require_replication_for_strong_claim)

        # 1. Theory ledger (working hypotheses; revisions preserved).
        self._build_theory(bundle)

        # 2. Claims + evidence map + strength + forbidden detection.
        claim_specs = bundle.get("claims", []) or []
        safety_failed = self._safety_failed(bundle)
        for spec in claim_specs[: self.max_claims]:
            self._ingest_claim(spec, detector, evaluator, safety_failed)

        # 3. Counterevidence (as visible as evidence).
        ce_records = CounterEvidenceAnalyzer().detect(bundle)
        self.counterevidence = CounterEvidenceAnalyzer.summary(ce_records)

        # 4. Forbidden-claim scan across all claim texts.
        all_text = "\n".join(c.text for c in self.registry.claims)
        self.forbidden = ForbiddenClaimDetector.summary(detector.scan(all_text))

        # 5. Limitations (mandatory + evidence-derived; linked to claims).
        claim_ids = [c.claim_id for c in self.registry.claims]
        lim_list = LimitationsBuilder().build(bundle, claim_refs=claim_ids)
        self.limitations = LimitationsBuilder.summary(lim_list)

        # 6. Safe abstracts (claim-constrained).
        self._build_abstracts()

        # 7. Publication dossier (draft only).
        self.dossier = PublicationDossierBuilder().build(
            claim_registry=self.registry.to_dict(),
            evidence_map=self.evidence_map.to_dict(),
            counterevidence=self.counterevidence,
            forbidden=self.forbidden,
            limitations=self.limitations,
            abstract=self.abstracts.get(AbstractVariant.TECHNICAL_PREPRINT, ""),
            safety_failed=safety_failed,
            baseline_status=str((bundle.get("research_baseline", {}) or {}).get(
                "baseline_status", "")),
            cycle_stage=str((bundle.get("research_cycle", {}) or {}).get(
                "current_cycle_stage", ""))).to_dict()

        # 8. ClaimGuard bridge over generated text.
        self._run_claim_guard()

        return {"refused": False,
                "claim_count": len(self.registry.claims),
                "readiness": self.dossier.get("publication_readiness_status")}

    # -- helpers ------------------------------------------------------------

    def _build_theory(self, bundle: Dict[str, Any]) -> None:
        for t in bundle.get("theories", []) or []:
            self.theory.add(TheoryStatement(
                theory_id=str(t.get("theory_id", f"theory_{len(self.theory.statements)+1}")),
                area=str(t.get("area", "architecture evolution")),
                text=str(t.get("text", "")),
                status=str(t.get("status", TheoryStatus.WORKING_HYPOTHESIS)),
                evidence_refs=list(t.get("evidence_refs", [])),
                counterevidence_refs=list(t.get("counterevidence_refs", []))))

    def _ingest_claim(self, spec: Dict[str, Any],
                      detector: ForbiddenClaimDetector,
                      evaluator: ClaimStrengthEvaluator,
                      safety_failed: bool) -> None:
        claim_id = str(spec.get("claim_id",
                                f"claim_{len(self.registry.claims)+1}"))
        text = str(spec.get("text", ""))
        category = str(spec.get("category", ClaimCategory.ARCHITECTURE))

        # Map evidence (many-to-many).
        evidence_refs: List[str] = []
        for ev in spec.get("evidence", []) or []:
            mapped = MappedEvidence(
                evidence_id=str(ev.get("evidence_id", "")),
                source=str(ev.get("source", "operator_notes")),
                role=str(ev.get("role", EvidenceRole.CONTEXTUALIZES)),
                detail=str(ev.get("detail", "")))
            self.evidence_map.map_evidence(claim_id, mapped)
            evidence_refs.append(mapped.evidence_id)

        # Forbidden assertion -> forbidden claim (blocked, not deleted).
        if detector.has_blocking_assertion(text):
            self.registry.add(ScientificClaim(
                claim_id=claim_id, text=text, category=ClaimCategory.FORBIDDEN,
                status=ClaimStatus.FORBIDDEN, evidence_refs=evidence_refs,
                missing_evidence_reason=spec.get("missing_evidence_reason", ""),
                detail="asserted a forbidden inner-state claim; blocked"))
            return

        factors = dict(spec.get("factors", {}) or {})
        if safety_failed:
            factors.setdefault("safety_failed", True)
        # Derive a couple of factors from the mapping when not explicit.
        if self.evidence_map.has_contradiction(claim_id):
            factors.setdefault("contradictory_evidence", True)
        score = evaluator.evaluate(factors)
        status = self._status_from(score, factors, claim_id, evidence_refs)

        self.registry.add(ScientificClaim(
            claim_id=claim_id, text=text, category=category, status=status,
            evidence_refs=evidence_refs,
            counterevidence_refs=self.evidence_map.against_refs(claim_id),
            missing_evidence_reason=str(spec.get("missing_evidence_reason", "")),
            strength=score.strength,
            detail=score.detail))

    def _status_from(self, score, factors: Dict[str, Any], claim_id: str,
                     evidence_refs: List[str]) -> str:
        if factors.get("falsified_core"):
            return ClaimStatus.FALSIFIED
        if score.strength == ClaimStrength.BLOCKED:
            # Blocked by safety (not falsified) -> requires more evidence.
            return ClaimStatus.REQUIRES_MORE_EVIDENCE
        if factors.get("contradictory_evidence") and \
                not self.evidence_map.has_support(claim_id):
            return ClaimStatus.CONTRADICTED
        if score.strength == ClaimStrength.STRONG:
            return ClaimStatus.SUPPORTED
        if score.strength == ClaimStrength.MODERATE:
            return ClaimStatus.PARTIALLY_SUPPORTED
        if score.strength == ClaimStrength.WEAK:
            return ClaimStatus.WEAKLY_SUPPORTED
        if score.strength == ClaimStrength.INCONCLUSIVE:
            return ClaimStatus.INCONCLUSIVE
        # strength NONE
        if not evidence_refs:
            return ClaimStatus.UNSUPPORTED
        return ClaimStatus.REQUIRES_MORE_EVIDENCE

    def _build_abstracts(self) -> None:
        claims = [c.to_dict() for c in self.registry.claims]
        supported = [c for c in claims if c["status"] in
                     (ClaimStatus.SUPPORTED, ClaimStatus.PARTIALLY_SUPPORTED)]
        weak = [c for c in claims
                if c["status"] == ClaimStatus.WEAKLY_SUPPORTED]
        inconclusive = [c for c in claims
                        if c["status"] == ClaimStatus.INCONCLUSIVE]
        negatives = [c for c in claims
                     if c["category"] == ClaimCategory.NEGATIVE_RESULT]
        builder = ScientificAbstractBuilder()
        self.abstracts = builder.build_all(
            supported_claims=supported, weak_claims=weak,
            inconclusive_claims=inconclusive, negative_results=negatives,
            limitations=self.limitations.get("limitations", []))

    def _run_claim_guard(self) -> None:
        items = {
            "claim_registry": "\n".join(c.text for c in self.registry.claims),
            "theory_ledger": "\n".join(
                s.text for s in self.theory.statements),
        }
        for variant, text in self.abstracts.items():
            items[f"abstract:{variant}"] = text
        items["publication_dossier"] = str(self.dossier.get("sections", {})
                                            .get("abstract", ""))
        self.claim_guard.scan_many(items)

    @staticmethod
    def _safety_failed(bundle: Dict[str, Any]) -> bool:
        rb = bundle.get("research_baseline", {}) or {}
        safety = bundle.get("safety", {}) or {}
        intake = bundle.get("implementation_intake", {}) or {}
        return (rb.get("safety_boundary_status") == "boundary_failed"
                or int(safety.get("critical_regression_count", 0) or 0) > 0
                or int(intake.get("critical_safety_regression_count", 0)
                       or 0) > 0)

    # -- integration views --------------------------------------------------

    def scientific_claims_status(self) -> Dict[str, Any]:
        idx = self.registry.index()
        readiness = self.dossier.get("publication_readiness_status",
                                     PublicationReadinessStatus.INCONCLUSIVE)
        return {
            "scientific_claims_enabled": True,
            "scientific_claim_count": idx["scientific_claim_count"],
            "supported_claim_count": idx["supported_claim_count"],
            "weakly_supported_claim_count": idx["weakly_supported_claim_count"],
            "partially_supported_claim_count": idx[
                "partially_supported_claim_count"],
            "inconclusive_claim_count": idx["inconclusive_claim_count"],
            "unsupported_claim_count": idx["unsupported_claim_count"],
            "contradicted_claim_count": idx["contradicted_claim_count"],
            "falsified_claim_count": idx["falsified_claim_count"],
            "forbidden_claim_count": idx["forbidden_claim_count"],
            "theory_statement_count": self.theory.to_dict()[
                "theory_statement_count"],
            "evidence_mapping_count": self.evidence_map.evidence_mapping_count,
            "counterevidence_count": self.counterevidence.get(
                "counterevidence_count", 0),
            "limitation_count": self.limitations.get("limitation_count", 0),
            "publication_readiness_status": readiness,
            "claimguard_block_count": self.claim_guard.claimguard_block_count,
            "claimguard_status": ("blocked" if self.claim_guard.any_blocked
                                  else "clean"),
            "claim_safety_block_count": self.safety.rejected_count,
            "latest_scientific_claim_report_path": self._report_path(),
            "proves_consciousness": False, "creates_release": False,
            "runs_git": False, "calls_github": False, "modifies_source": False,
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "SCIENTIFIC_CLAIM_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.scientific_claims_status()

    def experiment_suggestions(self) -> List[Dict[str, str]]:
        """Claim-gap -> future experiment/implementation suggestions."""
        out: List[Dict[str, str]] = []
        types = {r.get("counter_type")
                 for r in self.counterevidence.get("records", [])}
        if "missing_live_data" in types:
            out.append({"gap": "missing_live_data",
                        "experiment": "live_field_evidence_experiment"})
        if "failed_replication" in types or any(
                c.status == ClaimStatus.REQUIRES_MORE_EVIDENCE
                for c in self.registry.claims):
            out.append({"gap": "weak_replication",
                        "experiment": "replication_protocol_pack"})
        if "human_label_dependency" in types:
            out.append({"gap": "label_contamination",
                        "experiment": "contamination_mitigation_experiment"})
        if "fixture_overfit" in types:
            out.append({"gap": "fixture_overfit",
                        "experiment": "falsification_control_pack"})
        return out

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ScientificClaimReportBuilder

        return ScientificClaimReportBuilder(self).write()
