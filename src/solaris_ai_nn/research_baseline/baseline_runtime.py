"""Research baseline runtime -- turn a validated baseline into a research snapshot.

:class:`ResearchBaselineRuntime` consumes the post-merge assimilation artifacts
and builds the full research baseline: a local version record, snapshot manifest,
reproducibility bundle, capability map, limitation registry, safety boundary
statement, validation summary, comparison anchors, next-cycle roadmap, and
operator runbook -- writing local metadata/reports only. It creates no Git tag /
release / branch / PR, calls no Git/GitHub, modifies no source, runs no
validation command, runs no external agent, and controls no feeders/hardware/
network/shell.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .baseline_version import (
    BaselineVersionStatus,
    ResearchBaselineVersion,
)
from .capability_map import BaselineCapabilityMap
from .comparison_anchors import ComparisonAnchorSet
from .limitation_registry import build_limitation_registry
from .operator_runbook import build_operator_runbook
from .repro_bundle import ReproBundleBuilder
from .roadmap_reset import build_roadmap_reset
from .safety import ResearchBaselineSafetyValidator
from .safety_boundary_statement import SafetyBoundaryStatement
from .snapshot_manifest import ResearchSnapshotManifest
from .validation_summary import BaselineValidationSummary


@dataclass
class ResearchBaselineRuntime:
    """Bounded, read-only builder of a versioned research baseline."""

    state_dir: str = ".solaris_ai_nn_research_baseline"
    baseline_id: str = "research_baseline_v1"
    parent_baseline_id: str = ""
    post_merge_report_path: Optional[str] = None
    baseline_registry_path: Optional[str] = None
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_safety_validation: bool = True
    require_test_validation: bool = True
    require_claimguard_validation: bool = True

    safety: ResearchBaselineSafetyValidator = field(
        default_factory=ResearchBaselineSafetyValidator, init=False)
    version: Any = field(default=None, init=False)
    snapshot: Dict[str, Any] = field(default_factory=dict, init=False)
    repro: Dict[str, Any] = field(default_factory=dict, init=False)
    capability: Dict[str, Any] = field(default_factory=dict, init=False)
    limitations: Dict[str, Any] = field(default_factory=dict, init=False)
    safety_boundary: Dict[str, Any] = field(default_factory=dict, init=False)
    validation: Dict[str, Any] = field(default_factory=dict, init=False)
    anchors: Dict[str, Any] = field(default_factory=dict, init=False)
    roadmap: Dict[str, Any] = field(default_factory=dict, init=False)
    runbook: Dict[str, Any] = field(default_factory=dict, init=False)
    _repro_obj: Any = field(default=None, init=False)
    _runbook_obj: Any = field(default=None, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        self._bundle = dict(bundle or {})

    # -- build --------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        b = self._bundle
        post_merge = b.get("post_merge", {}) or {}
        intake = b.get("implementation_intake", {}) or {}

        # 1. Snapshot manifest (index artifacts; missing/corrupt visible).
        snap = ResearchSnapshotManifest()
        for atype, spec in (b.get("snapshot_artifacts", {}) or {}).items():
            spec = spec or {}
            snap.index(atype, path=spec.get("path", ""),
                       payload=spec.get("payload"),
                       negative_evidence=bool(spec.get("negative_evidence")))
        self.snapshot = snap.to_dict()

        # 2. Validation summary.
        vsum = BaselineValidationSummary().build(
            validation_results=b.get("validation_results", {}), intake=intake)
        self.validation = vsum.to_dict()

        # 3. Safety boundary statement.
        sbs = SafetyBoundaryStatement().build(
            safety_artifacts=b.get("safety_artifacts", {}))
        self.safety_boundary = sbs.to_dict()

        # 4. Limitation registry.
        limreg = build_limitation_registry(
            post_merge=post_merge, intake=intake, snapshot=self.snapshot,
            validation=self.validation)
        self.limitations = limreg.to_dict()

        # 5. Determine the version status (safety dominates).
        critical_safety_failed = (vsum.safety_failed
                                  or not sbs.all_held
                                  or limreg.critical_count > 0
                                  or int(post_merge.get(
                                      "critical_regression_count", 0) or 0) > 0)
        required_validation_missing = bool(vsum.required_missing)
        blocked_upstream = (
            post_merge.get("candidate_baseline_status") in (
                "blocked_by_safety", "blocked_by_tests",
                "blocked_by_falsification", "rollback_recommended")
            or post_merge.get("rollback_recommendation_status") in (
                "rollback_recommended", "block_baseline"))

        known_blockers = list(post_merge.get("unresolved_blockers", []) or [])
        if blocked_upstream:
            known_blockers.append(
                f"post-merge status: "
                f"{post_merge.get('candidate_baseline_status')}")
        known_warnings = self._collect_warnings(vsum, limreg)

        requested = self._requested_status(post_merge)
        self.version = ResearchBaselineVersion().assign(
            baseline_version_id=self.baseline_id,
            candidate_baseline_id=post_merge.get("candidate_baseline_id", ""),
            parent_baseline_id=self.parent_baseline_id
            or post_merge.get("current_baseline_id", ""),
            requested_status=requested, known_warnings=known_warnings,
            known_blockers=known_blockers,
            critical_safety_failed=critical_safety_failed,
            required_validation_missing=required_validation_missing,
            source_post_merge_report=self.post_merge_report_path or "",
            source_baseline_registry_entry=self.baseline_registry_path or "",
            operator_confirmation_refs=list(
                b.get("operator_confirmation_refs", [])),
            validation_refs=["validation_summary"],
            safety_refs=["safety_boundary_statement"],
            limitations=[l["category"] for l in
                         self.limitations.get("limitations", [])])

        # 6. Capability map.
        self.capability = BaselineCapabilityMap().build(
            evidence=b.get("capability_evidence", {})).to_dict()

        # 7. Comparison anchors.
        self.anchors = ComparisonAnchorSet().build(
            parent_baseline_id=self.version.parent_baseline_id,
            previous_validated_id=b.get("previous_validated_id", ""),
            available_anchors=b.get("available_anchors", {})).to_dict()
        # Missing anchors become limitations (kept visible).
        for lim in self.anchors.get("missing_anchor_limitations", []):
            self.limitations.setdefault("limitations", [])

        # 8. Reproducibility bundle.
        self._repro_obj = ReproBundleBuilder().build(
            baseline_version_id=self.baseline_id, snapshot=self.snapshot,
            known_warnings=known_warnings, state_dir=self.state_dir)
        self.repro = self._repro_obj.to_dict()

        # 9. Roadmap reset.
        self.roadmap = build_roadmap_reset(
            validated=self.version.validated, blocked=self.version.blocked,
            limitations=self.limitations, validation=self.validation).to_dict()

        # 10. Operator runbook.
        self._runbook_obj = build_operator_runbook(
            baseline_version_id=self.baseline_id, status=self.version.status)
        self.runbook = self._runbook_obj.to_dict()
        return {"refused": False, "baseline_status": self.version.status}

    @staticmethod
    def _requested_status(post_merge: Dict[str, Any]) -> str:
        cand = post_merge.get("candidate_baseline_status")
        if cand == "validated":
            return BaselineVersionStatus.VALIDATED
        if cand == "validated_with_warnings":
            return BaselineVersionStatus.VALIDATED_WITH_WARNINGS
        if cand in ("blocked_by_safety", "blocked_by_tests",
                    "blocked_by_falsification", "rollback_recommended"):
            return BaselineVersionStatus.BLOCKED
        return BaselineVersionStatus.CANDIDATE

    @staticmethod
    def _collect_warnings(vsum: Any, limreg: Any) -> List[str]:
        warnings: List[str] = []
        if vsum.has_warnings:
            warnings.append("validation passed with warnings")
        for l in limreg.limitations:
            if l.severity == "major":
                warnings.append(f"major limitation: {l.category}")
            elif l.severity == "warning":
                warnings.append(f"limitation: {l.category}")
        return warnings

    # -- integration views --------------------------------------------------

    def architecture_starting_point(self) -> Dict[str, Any]:
        """The clean starting point exported to the Architecture Evolution Lab."""
        return {
            "research_baseline_version": self.version.to_dict()
            if self.version else None,
            "capability_map": self.capability,
            "limitation_registry": self.limitations,
            "next_cycle_roadmap": self.roadmap,
            "comparison_anchors": self.anchors,
            "missing_evidence": self.snapshot.get("missing", []),
        }

    def research_baseline_status(self) -> Dict[str, Any]:
        v = self.version
        cap = self.capability
        lim = self.limitations
        sbs = self.safety_boundary
        return {
            "research_baseline_enabled": True,
            "current_baseline_version_id": self.baseline_id,
            "baseline_status": v.status if v else None,
            "research_baseline_version_count": 1 if v else 0,
            "validated_baseline_count": 1 if (v and v.validated) else 0,
            "blocked_baseline_count": 1 if (v and v.blocked) else 0,
            "snapshot_artifact_count": self.snapshot.get(
                "snapshot_artifact_count", 0),
            "missing_snapshot_artifact_count": self.snapshot.get(
                "missing_snapshot_artifact_count", 0),
            "capability_count": cap.get("capability_count", 0),
            "validated_capability_count": cap.get(
                "validated_capability_count", 0),
            "limitation_count": lim.get("limitation_count", 0),
            "critical_limitation_count": lim.get("critical_limitation_count", 0),
            "safety_boundary_status": "all_held" if sbs.get("all_held")
            else "boundary_failed",
            "safety_boundary_pass_count": sbs.get(
                "safety_boundary_pass_count", 0),
            "safety_boundary_fail_count": sbs.get(
                "safety_boundary_fail_count", 0),
            "validation_status": "blocks" if self.validation.get(
                "blocks_validation") else "ok",
            "validation_pass_count": self.validation.get(
                "validation_pass_count", 0),
            "validation_missing_count": self.validation.get(
                "validation_missing_count", 0),
            "comparison_anchor_count": self.anchors.get(
                "comparison_anchor_count", 0),
            "roadmap_item_count": self.roadmap.get("roadmap_item_count", 0),
            "next_roadmap_item_count": self.roadmap.get("roadmap_item_count", 0),
            "research_baseline_safety_block_count": self.safety.rejected_count,
            "latest_research_baseline_report_path": self._report_path(),
            "is_git_tag": False, "is_github_release": False,
            "is_product_release": False, "modifies_source": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "RESEARCH_BASELINE_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot_view(self) -> Dict[str, Any]:
        return self.research_baseline_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ResearchBaselineReportBuilder

        return ResearchBaselineReportBuilder(self).write()
