"""Post-merge evidence assimilation -- gather every source, hide nothing.

:class:`PostMergeEvidenceAssimilator` collects the implementation-intake audits
and the post-merge validation results into one bundle, surfacing conflicts and
missing evidence rather than averaging them away. Safety evidence has priority,
negative evidence is never discarded, and inconclusive evidence is valid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceVerdict:
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CONFLICTING = "conflicting"
    MISSING = "missing"
    INCONCLUSIVE = "inconclusive"

    ALL = (POSITIVE, NEGATIVE, CONFLICTING, MISSING, INCONCLUSIVE)


@dataclass
class EvidenceAssimilationFinding:
    """One assimilated evidence source + its verdict (conflicts kept visible)."""

    source: str
    verdict: str
    detail: str = ""
    safety_relevant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "verdict": self.verdict,
                "detail": self.detail, "safety_relevant": self.safety_relevant}


@dataclass
class AssimilatedEvidenceBundle:
    """The full assimilated evidence bundle for a candidate baseline."""

    findings: List[EvidenceAssimilationFinding] = field(default_factory=list)
    missing_sources: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    @property
    def safety_negative(self) -> bool:
        return any(f.safety_relevant and f.verdict == EvidenceVerdict.NEGATIVE
                   for f in self.findings)

    def counts(self) -> Dict[str, int]:
        out = {v: 0 for v in EvidenceVerdict.ALL}
        for f in self.findings:
            out[f.verdict] = out.get(f.verdict, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "counts": self.counts(),
            "missing_sources": list(self.missing_sources),
            "conflicts": list(self.conflicts),
            "safety_negative": self.safety_negative,
            "note": "conflicts and missing evidence stay visible; safety "
                    "evidence has priority; negative/inconclusive evidence is "
                    "preserved",
        }


@dataclass
class PostMergeEvidenceAssimilator:
    """Assimilates intake + validation evidence, surfacing conflicts/gaps."""

    def assimilate(self, *, intake: Optional[Dict[str, Any]] = None,
                   validation: Optional[Dict[str, Any]] = None,
                   architecture_evidence: Optional[Dict[str, Any]] = None,
                   ) -> AssimilatedEvidenceBundle:
        intake = intake or {}
        validation = validation or {}
        bundle = AssimilatedEvidenceBundle()

        # -- implementation-intake audits ------------------------------------
        merge_status = intake.get("merge_recommendation_status")
        if merge_status:
            positive = merge_status in ("recommend_merge",
                                        "recommend_merge_with_warnings")
            # The intake recommendation is *advisory*; the actual safety signal
            # comes from the critical-regression count and the validation
            # safety-invariant run, not this recommendation string.
            bundle.findings.append(EvidenceAssimilationFinding(
                "intake_merge_recommendation",
                EvidenceVerdict.POSITIVE if positive
                else EvidenceVerdict.NEGATIVE,
                f"intake recommended: {merge_status}",
                safety_relevant=False))
        else:
            bundle.missing_sources.append("implementation_intake_report")

        crit = int(intake.get("critical_safety_regression_count", 0) or 0)
        bundle.findings.append(EvidenceAssimilationFinding(
            "intake_safety_regression",
            EvidenceVerdict.NEGATIVE if crit else EvidenceVerdict.POSITIVE,
            f"{crit} critical safety regression(s) in intake",
            safety_relevant=True))

        spec_status = intake.get("spec_compliance_status")
        if spec_status:
            bundle.findings.append(EvidenceAssimilationFinding(
                "intake_spec_compliance",
                EvidenceVerdict.POSITIVE if spec_status == "satisfied"
                else EvidenceVerdict.INCONCLUSIVE
                if spec_status == "partially_satisfied"
                else EvidenceVerdict.NEGATIVE,
                f"spec compliance: {spec_status}"))

        # -- post-merge validation results -----------------------------------
        v_artifacts = {a["artifact_type"]: a
                       for a in validation.get("artifacts", [])}
        for atype, finding_safety in (
                ("full_test_run", False), ("safety_invariant_run", True),
                ("claimguard_run", True), ("mini_soak", False),
                ("falsification_replay", False), ("example_run", False)):
            art = v_artifacts.get(atype)
            if art is None or not art.get("present"):
                bundle.missing_sources.append(atype)
                bundle.findings.append(EvidenceAssimilationFinding(
                    f"validation_{atype}", EvidenceVerdict.MISSING,
                    "validation artifact not supplied",
                    safety_relevant=finding_safety))
                continue
            passed = art.get("passed")
            verdict = (EvidenceVerdict.POSITIVE if passed is True
                       else EvidenceVerdict.NEGATIVE if passed is False
                       else EvidenceVerdict.INCONCLUSIVE)
            bundle.findings.append(EvidenceAssimilationFinding(
                f"validation_{atype}", verdict,
                f"validation {atype}: passed={passed}",
                safety_relevant=finding_safety))

        # -- architecture evidence (optional) --------------------------------
        if architecture_evidence:
            bundle.findings.append(EvidenceAssimilationFinding(
                "architecture_evidence", EvidenceVerdict.INCONCLUSIVE,
                "architecture-evolution evidence attached for future use"))

        # -- conflict detection (intake says ok but validation fails, etc.) --
        intake_ok = merge_status in ("recommend_merge",
                                     "recommend_merge_with_warnings")
        validation_failed = any(
            f.verdict == EvidenceVerdict.NEGATIVE
            and f.source.startswith("validation_") for f in bundle.findings)
        if intake_ok and validation_failed:
            bundle.conflicts.append(
                "intake recommended merge but post-merge validation failed")
        if crit and intake_ok:
            bundle.conflicts.append(
                "intake recommended merge despite a critical safety regression")
        return bundle
