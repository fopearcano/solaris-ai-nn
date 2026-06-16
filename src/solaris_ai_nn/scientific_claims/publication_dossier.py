"""Publication dossier -- a draft evidence compilation, never marketing.

:class:`PublicationDossierBuilder` assembles the publication-grade evidence
dossier (title, abstract, research question, architecture summary, method,
evidence/claim/counterevidence tables, experiments, controls, replication and
falsification status, safety boundaries, limitations, negative results, future
work, explicitly rejected forbidden claims, and an artifact appendix). The dossier
must include negative and inconclusive results and safety boundaries, must not
assert unsupported claims, and is a draft/report only -- not a release.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .claim_registry import ClaimStatus


class PublicationReadinessStatus:
    READY_AS_INTERNAL_REPORT = "ready_as_internal_report"
    READY_AS_PREPRINT_DRAFT = "ready_as_preprint_draft"
    READY_WITH_MAJOR_LIMITATIONS = "ready_with_major_limitations"
    NOT_READY_MISSING_EVIDENCE = "not_ready_missing_evidence"
    BLOCKED_BY_COUNTEREVIDENCE = "blocked_by_counterevidence"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_FORBIDDEN_CLAIMS = "blocked_by_forbidden_claims"
    INCONCLUSIVE = "inconclusive"

    ALL = (READY_AS_INTERNAL_REPORT, READY_AS_PREPRINT_DRAFT,
           READY_WITH_MAJOR_LIMITATIONS, NOT_READY_MISSING_EVIDENCE,
           BLOCKED_BY_COUNTEREVIDENCE, BLOCKED_BY_SAFETY,
           BLOCKED_BY_FORBIDDEN_CLAIMS, INCONCLUSIVE)

    BLOCKED = (BLOCKED_BY_COUNTEREVIDENCE, BLOCKED_BY_SAFETY,
               BLOCKED_BY_FORBIDDEN_CLAIMS)


@dataclass
class PublicationDossier:
    """The assembled dossier sections + readiness status."""

    readiness: str
    sections: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publication_readiness_status": self.readiness,
            "is_release": False, "is_marketing": False, "is_draft": True,
            "sections": self.sections,
            "note": "draft evidence compilation only; includes negative, "
                    "inconclusive results and safety boundaries; asserts no "
                    "unsupported claim and is not a release",
        }


@dataclass
class PublicationDossierBuilder:
    """Builds the draft publication dossier and determines readiness."""

    def build(self, *,
              claim_registry: Dict[str, Any],
              evidence_map: Dict[str, Any],
              counterevidence: Dict[str, Any],
              forbidden: Dict[str, Any],
              limitations: Dict[str, Any],
              abstract: str = "",
              safety_failed: bool = False,
              baseline_status: str = "",
              cycle_stage: str = "",
              research_question: str = "",
              architecture_summary: str = "",
              ) -> PublicationDossier:
        claims = claim_registry.get("claims", [])
        supported = [c for c in claims if c.get("status") in
                     (ClaimStatus.SUPPORTED, ClaimStatus.WEAKLY_SUPPORTED,
                      ClaimStatus.PARTIALLY_SUPPORTED)]
        falsified = [c for c in claims if c.get("status") in
                     (ClaimStatus.FALSIFIED, ClaimStatus.CONTRADICTED)]
        inconclusive = [c for c in claims
                        if c.get("status") == ClaimStatus.INCONCLUSIVE]
        negatives = [c for c in claims if c.get("category") ==
                     "negative_result_claim"]

        readiness = self._determine_readiness(
            supported=supported, claims=claims,
            counterevidence=counterevidence, forbidden=forbidden,
            safety_failed=safety_failed, limitations=limitations)

        sections = {
            "title": "Solaris-AI-NN: Evidence Dossier (Draft)",
            "abstract": abstract,
            "research_question": research_question or (
                "What operational structures, sensorium-native signs, and "
                "action-consequence patterns are supported by the current "
                "bounded evidence?"),
            "architecture_summary": architecture_summary or (
                "A bounded recurrent substrate with plural sensorium, "
                "perceptual metabolism, and a closed research/evidence cycle."),
            "method": ("Bounded local fixtures and read-only feeds; evidence is "
                       "mapped to claims; counterevidence and limitations are "
                       "preserved; ClaimGuard scans all generated text."),
            "evidence_table": evidence_map.get("mapping", {}),
            "claim_table": claims,
            "counterevidence_table": counterevidence.get("records", []),
            "experiments": [c.get("category") for c in claims],
            "controls": "control/ablation/null comparisons where available",
            "replication_status": self._status_line(claims,
                                                     "replication_claim"),
            "falsification_status": (
                f"{len(falsified)} claim(s) falsified/contradicted; preserved"),
            "safety_boundaries": (
                "no actuation, no hardware/feeder/network/shell, no source "
                "self-rewrite, no Git/GitHub automation, no unsupported "
                "consciousness/life/agency claims"),
            "limitations": limitations.get("limitations", []),
            "negative_results": negatives,
            "inconclusive_results": inconclusive,
            "future_work": self._future_work(claims, counterevidence),
            "forbidden_claims_explicitly_rejected": [
                "consciousness", "sentience", "biological life", "personhood",
                "agency", "free will", "emotion/feeling", "understanding",
                "self-awareness", "subjective experience",
                "autonomous self-improvement"],
            "appendix_artifact_index": claim_registry.get("note", ""),
        }
        return PublicationDossier(readiness=readiness, sections=sections)

    @staticmethod
    def _status_line(claims: List[Dict], category: str) -> str:
        n = sum(1 for c in claims if c.get("category") == category)
        return f"{n} {category} entry(ies)"

    @staticmethod
    def _future_work(claims: List[Dict], counterevidence: Dict[str, Any],
                     ) -> List[str]:
        work: List[str] = []
        types = {r.get("counter_type") for r in counterevidence.get("records", [])}
        if "missing_live_data" in types:
            work.append("collect live-field evidence")
        if "failed_replication" in types or any(
                c.get("status") == "requires_more_evidence" for c in claims):
            work.append("run additional replication arms")
        if "fixture_overfit" in types:
            work.append("add falsification/control packs against fixture overfit")
        if "human_label_dependency" in types:
            work.append("add label-contamination mitigation experiments")
        return work or ["strengthen controls and replication for weak claims"]

    @staticmethod
    def _determine_readiness(*, supported, claims, counterevidence, forbidden,
                             safety_failed, limitations) -> str:
        if forbidden.get("blocks_publication"):
            return PublicationReadinessStatus.BLOCKED_BY_FORBIDDEN_CLAIMS
        if safety_failed:
            return PublicationReadinessStatus.BLOCKED_BY_SAFETY
        if counterevidence.get("blocking_counterevidence_count", 0) > 0:
            return PublicationReadinessStatus.BLOCKED_BY_COUNTEREVIDENCE
        if not claims:
            return PublicationReadinessStatus.NOT_READY_MISSING_EVIDENCE
        if not supported:
            return PublicationReadinessStatus.INCONCLUSIVE
        strong = [c for c in supported if c.get("status") == "supported"]
        major_lims = limitations.get("limitation_count", 0) > 6
        if strong and not major_lims:
            return PublicationReadinessStatus.READY_AS_PREPRINT_DRAFT
        if strong:
            return PublicationReadinessStatus.READY_WITH_MAJOR_LIMITATIONS
        return PublicationReadinessStatus.READY_AS_INTERNAL_REPORT
