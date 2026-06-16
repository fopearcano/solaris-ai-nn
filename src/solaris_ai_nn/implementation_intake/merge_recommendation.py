"""Merge recommendation -- advisory only; a human operator decides.

:class:`MergeRecommendationBuilder` aggregates the diff/spec/test/safety/
ClaimGuard/coverage audits into a single advisory :class:`MergeRecommendation`.
It does not merge, approve, open, or create a pull request. A safety-critical
failure or missing critical evidence blocks the recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MergeRecommendationStatus:
    RECOMMEND_MERGE = "recommend_merge"
    RECOMMEND_MERGE_WITH_WARNINGS = "recommend_merge_with_warnings"
    RECOMMEND_REVISIONS = "recommend_revisions"
    BLOCK_MERGE_DUE_TO_SAFETY = "block_merge_due_to_safety"
    BLOCK_MERGE_DUE_TO_TESTS = "block_merge_due_to_tests"
    BLOCK_MERGE_DUE_TO_SPEC_NONCOMPLIANCE = \
        "block_merge_due_to_spec_noncompliance"
    BLOCK_MERGE_DUE_TO_MISSING_EVIDENCE = "block_merge_due_to_missing_evidence"
    INCONCLUSIVE = "inconclusive"

    ALL = (RECOMMEND_MERGE, RECOMMEND_MERGE_WITH_WARNINGS, RECOMMEND_REVISIONS,
           BLOCK_MERGE_DUE_TO_SAFETY, BLOCK_MERGE_DUE_TO_TESTS,
           BLOCK_MERGE_DUE_TO_SPEC_NONCOMPLIANCE,
           BLOCK_MERGE_DUE_TO_MISSING_EVIDENCE, INCONCLUSIVE)

    BLOCKING = (BLOCK_MERGE_DUE_TO_SAFETY, BLOCK_MERGE_DUE_TO_TESTS,
                BLOCK_MERGE_DUE_TO_SPEC_NONCOMPLIANCE,
                BLOCK_MERGE_DUE_TO_MISSING_EVIDENCE)


@dataclass
class MergeBlocker:
    """One reason the merge cannot be recommended."""

    kind: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "detail": self.detail}


@dataclass
class MergeRecommendation:
    """The advisory merge recommendation (never executes a merge)."""

    status: str = MergeRecommendationStatus.INCONCLUSIVE
    rationale: str = ""
    blockers: List[MergeBlocker] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    considered: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status, "rationale": self.rationale,
            "blockers": [b.to_dict() for b in self.blockers],
            "blocker_count": len(self.blockers),
            "warnings": list(self.warnings), "considered": dict(self.considered),
            "advisory_only": True, "merges_pr": False, "approves_pr": False,
            "note": ("advisory only; the intake layer does not merge, approve, "
                     "open, or create pull requests -- a human operator decides"),
        }


@dataclass
class MergeRecommendationBuilder:
    """Builds the advisory merge recommendation from the audit results."""

    def build(self, *, manifest: Optional[Dict] = None,
              diff_audit: Optional[Dict] = None,
              spec_compliance: Optional[Dict] = None,
              test_audit: Optional[Dict] = None,
              safety_regression: Optional[Dict] = None,
              claimguard_audit: Optional[Dict] = None,
              coverage_matrix: Optional[Dict] = None,
              ) -> MergeRecommendation:
        manifest = manifest or {}
        diff_audit = diff_audit or {}
        spec_compliance = spec_compliance or {}
        test_audit = test_audit or {}
        safety_regression = safety_regression or {}
        claimguard_audit = claimguard_audit or {}
        coverage_matrix = coverage_matrix or {}

        rec = MergeRecommendation()
        rec.considered = {
            "spec_compliance": spec_compliance.get("counts"),
            "diff_blockers": diff_audit.get("blocker_count"),
            "test_passes": test_audit.get("passes"),
            "safety_max_severity": safety_regression.get("max_severity"),
            "claimguard_status": claimguard_audit.get("status"),
            "coverage_gaps": coverage_matrix.get("coverage_gap_count"),
        }

        # 1. Safety-critical regression or forbidden diff => block (highest).
        if safety_regression.get("critical_count", 0) or \
                diff_audit.get("forbidden_file_change_count", 0) or \
                diff_audit.get("blocker_count", 0):
            rec.blockers.append(MergeBlocker(
                "safety", "critical safety regression / forbidden change "
                "detected"))
        if claimguard_audit.get("blocks_readiness"):
            rec.blockers.append(MergeBlocker(
                "safety", "undisclaimed unsupported claim in generated docs"))

        # 2. Missing critical evidence (required artifacts) => block.
        critical_missing = manifest.get("blockers", [])
        if critical_missing:
            rec.blockers.append(MergeBlocker(
                "missing_evidence",
                f"missing critical artifact(s): {critical_missing}"))

        # 3. Test failures / missing safety tests => block.
        if test_audit and not test_audit.get("passes", True):
            rec.blockers.append(MergeBlocker(
                "tests", f"test blockers: {test_audit.get('blockers')}"))

        # 4. Spec non-compliance (blocking failures) => block.
        if spec_compliance.get("blocking_failure_count", 0):
            rec.blockers.append(MergeBlocker(
                "spec_noncompliance",
                f"{spec_compliance['blocking_failure_count']} blocking spec "
                "failure(s)"))

        # Warnings (non-blocking).
        rec.warnings.extend(test_audit.get("warnings", []))
        if diff_audit.get("warning_count", 0):
            rec.warnings.append(
                f"{diff_audit['warning_count']} diff warning(s)")
        if safety_regression.get("major_count", 0):
            rec.warnings.append(
                f"{safety_regression['major_count']} major safety finding(s) "
                "require operator review")
        if coverage_matrix.get("coverage_gap_count", 0):
            rec.warnings.append(
                f"{coverage_matrix['coverage_gap_count']} coverage gap(s)")

        rec.status, rec.rationale = self._decide(rec, spec_compliance,
                                                 test_audit, coverage_matrix)
        return rec

    @staticmethod
    def _decide(rec: MergeRecommendation, spec_compliance, test_audit,
                coverage_matrix):
        # Pick the most specific blocking status.
        kinds = {b.kind for b in rec.blockers}
        if "safety" in kinds:
            return (MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_SAFETY,
                    "a safety-critical issue blocks merge")
        if "tests" in kinds:
            return (MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_TESTS,
                    "failing or missing required tests block merge")
        if "spec_noncompliance" in kinds:
            return (
                MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_SPEC_NONCOMPLIANCE,
                "blocking spec requirements are not satisfied")
        if "missing_evidence" in kinds:
            return (MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_MISSING_EVIDENCE,
                    "critical evidence is missing")

        # No blockers: decide between merge / merge-with-warnings / revisions.
        satisfied = (spec_compliance.get("counts", {}) or {}).get("satisfied", 0)
        unknown = (spec_compliance.get("counts", {}) or {}).get("unknown", 0)
        if not test_audit and not spec_compliance:
            return (MergeRecommendationStatus.INCONCLUSIVE,
                    "insufficient evidence to recommend")
        if coverage_matrix.get("coverage_gap_count", 0) > 0 or unknown > 0:
            return (MergeRecommendationStatus.RECOMMEND_REVISIONS,
                    "coverage gaps / unknown requirements remain")
        if rec.warnings:
            return (MergeRecommendationStatus.RECOMMEND_MERGE_WITH_WARNINGS,
                    "no blockers; warnings should be reviewed")
        if satisfied:
            return (MergeRecommendationStatus.RECOMMEND_MERGE,
                    "evidence sufficient; no blockers or warnings")
        return (MergeRecommendationStatus.INCONCLUSIVE,
                "insufficient positive evidence to recommend merge")
