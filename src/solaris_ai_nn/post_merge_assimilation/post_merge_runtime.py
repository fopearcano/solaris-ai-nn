"""Post-merge assimilation runtime -- the bounded, read-only research ledger.

:class:`PostMergeAssimilationRuntime` ingests operator-provided local evidence
after an external human merge, registers a candidate baseline, assimilates the
evidence, compares it to the parent baseline, runs the regression watch, and
emits module-status / rollback / follow-up recommendations -- writing local
metadata and reports only. It runs no Git, calls no GitHub, creates/merges no
PR, modifies no source, executes no validation command, runs no external agent,
and controls no feeders/hardware/network/shell.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .baseline_comparison import BaselineComparison
from .baseline_registry import BaselineRecord, BaselineRegistry, BaselineStatus
from .evidence_assimilation import PostMergeEvidenceAssimilator
from .followup_queue import build_followup_queue
from .merge_manifest import PostMergeManifest
from .module_status_update import (
    ModuleStatusUpdateRecommendationBuilder,
    ModuleStatusUpdateType,
)
from .regression_watch import RegressionWatch
from .rollback_watch import RollbackWatch
from .safety import PostMergeAssimilationSafetyValidator
from .validation_ingest import PostMergeValidationIngest

# module-status recommendation -> baseline status
_STATUS_MAP = {
    ModuleStatusUpdateType.BLOCK_DUE_TO_SAFETY: BaselineStatus.BLOCKED_BY_SAFETY,
    ModuleStatusUpdateType.BLOCK_DUE_TO_FALSIFICATION:
        BaselineStatus.BLOCKED_BY_FALSIFICATION,
    ModuleStatusUpdateType.ROLLBACK_RECOMMENDED:
        BaselineStatus.ROLLBACK_RECOMMENDED,
    ModuleStatusUpdateType.RETEST_REQUIRED: BaselineStatus.CANDIDATE,
    ModuleStatusUpdateType.REGRESSION_WATCH: BaselineStatus.REGRESSION_WATCH,
    ModuleStatusUpdateType.VALIDATE_WITH_WARNING:
        BaselineStatus.VALIDATED_WITH_WARNINGS,
    ModuleStatusUpdateType.VALIDATE_CANDIDATE: BaselineStatus.VALIDATED,
    ModuleStatusUpdateType.PROMOTE_CANDIDATE: BaselineStatus.VALIDATED,
    ModuleStatusUpdateType.FREEZE_CANDIDATE: BaselineStatus.REGRESSION_WATCH,
    ModuleStatusUpdateType.KEEP_EXPERIMENTAL: BaselineStatus.CANDIDATE,
}


@dataclass
class PostMergeAssimilationRuntime:
    """Bounded read-only ledger: post-merge evidence -> baselines + reports."""

    state_dir: str = ".solaris_ai_nn_post_merge"
    merge_manifest_path: Optional[str] = None
    parent_baseline_id: str = ""
    candidate_baseline_id: str = "baseline_candidate"
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_safety_artifacts: bool = True
    require_test_artifacts: bool = True
    require_claimguard_artifacts: bool = True
    require_validation_artifacts: bool = True

    registry: BaselineRegistry = field(default=None, init=False)
    safety: PostMergeAssimilationSafetyValidator = field(
        default_factory=PostMergeAssimilationSafetyValidator, init=False)
    manifest: Any = field(default=None, init=False)
    candidate: Any = field(default=None, init=False)

    validation: Dict[str, Any] = field(default_factory=dict, init=False)
    evidence: Dict[str, Any] = field(default_factory=dict, init=False)
    comparison: Dict[str, Any] = field(default_factory=dict, init=False)
    regression: Dict[str, Any] = field(default_factory=dict, init=False)
    module_status: Dict[str, Any] = field(default_factory=dict, init=False)
    rollback: Dict[str, Any] = field(default_factory=dict, init=False)
    followup: Dict[str, Any] = field(default_factory=dict, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.registry = BaselineRegistry(state_dir=self.state_dir,
                                         persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    # -- input --------------------------------------------------------------

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        """Provide the operator's local post-merge evidence bundle."""
        self._bundle = dict(bundle or {})
        self.manifest = PostMergeManifest.from_dict(
            self._bundle.get("merge_manifest", {}))

    def register_parent(self, baseline_id: str, *, metrics: Optional[Dict] = None,
                        status: str = BaselineStatus.VALIDATED) -> BaselineRecord:
        rec = BaselineRecord(baseline_id=baseline_id, status=status,
                             metrics=dict(metrics or {}))
        self.registry.register(rec)
        if not self.parent_baseline_id:
            self.parent_baseline_id = baseline_id
        return rec

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bundle = self._bundle
        intake = bundle.get("implementation_intake", {}) or {}

        # 1. Ingest local validation artifacts (no validation is executed).
        self.validation = PostMergeValidationIngest().ingest(
            bundle.get("validation_results", {})).to_dict()

        # 2. Assimilate evidence (conflicts + gaps stay visible).
        self.evidence = PostMergeEvidenceAssimilator().assimilate(
            intake=intake, validation=self.validation,
            architecture_evidence=bundle.get("architecture_evidence")).to_dict()

        # 3. Compare candidate vs parent baseline.
        parent = self.registry.get(self.parent_baseline_id)
        parent_metrics = (parent.metrics if parent
                          else bundle.get("parent_metrics", {}))
        candidate_metrics = bundle.get("candidate_metrics", {})
        self.comparison = BaselineComparison().compare(
            parent_metrics=parent_metrics, candidate_metrics=candidate_metrics)

        # 4. Regression watch.
        self.regression = RegressionWatch().watch(
            comparison=self.comparison, evidence=self.evidence, intake=intake
        ).to_dict()

        # 5. Module status recommendation.
        self.module_status = ModuleStatusUpdateRecommendationBuilder().build(
            evidence=self.evidence, regression=self.regression,
            comparison=self.comparison, intake=intake,
            validation=self.validation,
            target_modules=bundle.get("target_modules", [])).to_dict()

        # 6. Rollback watch.
        self.rollback = RollbackWatch().build(
            regression=self.regression, evidence=self.evidence, intake=intake,
            validation=self.validation,
            manifest=self.manifest.to_dict() if self.manifest else {}).to_dict()

        # 7. Determine the candidate baseline status (safety dominates).
        status = self._baseline_status(intake)

        # 8. Register the candidate baseline (append-only).
        self.candidate = self._register_candidate(status, candidate_metrics,
                                                  bundle)

        # 9. Follow-up queue.
        validated = status in (BaselineStatus.VALIDATED,
                               BaselineStatus.VALIDATED_WITH_WARNINGS)
        self.followup = build_followup_queue(
            validation=self.validation, regression=self.regression,
            module_status=self.module_status, rollback=self.rollback,
            baseline_validated=validated).to_dict()
        return {"refused": False, "candidate_baseline_status": status}

    def _baseline_status(self, intake: Dict[str, Any]) -> str:
        rec_type = self.module_status.get("update_type",
                                          ModuleStatusUpdateType.UNKNOWN)
        status = _STATUS_MAP.get(rec_type, BaselineStatus.CANDIDATE)

        # Intake blocked-by-safety stays blocked unless the operator supplied
        # separate safety evidence that passes (section 14).
        safety_run = next((a for a in self.validation.get("artifacts", [])
                           if a.get("artifact_type") == "safety_invariant_run"),
                          None)
        safety_passed = bool(safety_run and safety_run.get("passed"))
        if intake.get("merge_recommendation_status") == \
                "block_merge_due_to_safety" and not safety_passed:
            return BaselineStatus.BLOCKED_BY_SAFETY

        # Safety/critical evidence gate from the safety validator.
        critical_safety_failed = (
            self.regression.get("critical_regression_count", 0) > 0
            or self.evidence.get("safety_negative", False))
        critical_missing = (
            self.require_validation_artifacts
            and self.validation.get("missing_validation_artifact_count", 0) > 0)
        gate = self.safety.validate_baseline_validation(
            critical_safety_failed=critical_safety_failed,
            critical_evidence_missing=critical_missing)
        if not gate.safe and status in (
                BaselineStatus.VALIDATED,
                BaselineStatus.VALIDATED_WITH_WARNINGS):
            # Cannot validate when safety fails or critical evidence is missing.
            return (BaselineStatus.BLOCKED_BY_SAFETY if critical_safety_failed
                    else BaselineStatus.REGRESSION_WATCH)
        return status

    def _register_candidate(self, status: str, metrics: Dict,
                            bundle: Dict) -> BaselineRecord:
        unresolved = list(self.rollback.get("triggers", []))
        rec = BaselineRecord(
            baseline_id=self.candidate_baseline_id,
            parent_baseline_id=self.parent_baseline_id,
            source_experiment_id=self.manifest.source_experiment_id
            if self.manifest else "",
            source_branch_spec_id=self.manifest.source_branch_spec_id
            if self.manifest else "",
            merge_manifest_path=self.merge_manifest_path or "",
            implementation_intake_path=self.manifest.
            source_implementation_intake_report if self.manifest else "",
            module_changes_summary=list(bundle.get("module_changes_summary",
                                                   [])),
            expected_effects=list(bundle.get("expected_effects", [])),
            observed_effects=[f["detail"] for f in
                              self.evidence.get("findings", [])][:12],
            known_risks=list(bundle.get("known_risks", [])),
            unresolved_blockers=unresolved,
            status=status, metrics=dict(metrics or {}))
        rec.set_status(status, reason=self.module_status.get("update_type", ""))
        return self.registry.register(rec)

    # -- integration views --------------------------------------------------

    def architecture_evidence(self) -> Dict[str, Any]:
        """Outputs usable by the Architecture Evolution Lab."""
        return {
            "baseline_record": self.candidate.to_dict() if self.candidate
            else None,
            "module_status_recommendation": self.module_status,
            "regression_watch": self.regression,
            "rollback_watch": self.rollback,
            "followup_queue": self.followup,
            "evidence_assimilation_bundle": self.evidence,
        }

    def post_merge_status(self) -> Dict[str, Any]:
        reg = self.registry.status()
        cand_status = self.candidate.status if self.candidate else None
        return {
            "post_merge_assimilation_enabled": True,
            "post_merge_manifest_count": 1 if self.manifest else 0,
            "baseline_record_count": reg["baseline_record_count"],
            "candidate_baseline_count": reg["candidate_baseline_count"],
            "validated_baseline_count": reg["validated_baseline_count"],
            "blocked_baseline_count": reg["blocked_baseline_count"],
            "current_baseline_id": (self.registry.latest_validated().baseline_id
                                    if self.registry.latest_validated()
                                    else self.parent_baseline_id or None),
            "candidate_baseline_id": self.candidate_baseline_id,
            "candidate_baseline_status": cand_status,
            "validation_artifact_count": self.validation.get(
                "validation_artifact_count", 0),
            "missing_validation_artifact_count": self.validation.get(
                "missing_validation_artifact_count", 0),
            "baseline_regression_count": self.regression.get(
                "baseline_regression_count", 0),
            "critical_regression_count": self.regression.get(
                "critical_regression_count", 0),
            "regression_watch_count": self.regression.get(
                "baseline_regression_count", 0),
            "module_status_recommendation_count": 1 if self.module_status else 0,
            "module_status_recommendation": self.module_status.get(
                "update_type"),
            "rollback_recommendation_status": self.rollback.get(
                "recommendation"),
            "rollback_watch_trigger_count": self.rollback.get(
                "rollback_watch_trigger_count", 0),
            "followup_queue_count": self.followup.get("followup_item_count", 0),
            "followup_item_count": self.followup.get("followup_item_count", 0),
            "post_merge_safety_block_count": self.safety.rejected_count,
            "latest_post_merge_report_path": self._report_path(),
            "modifies_source": False, "runs_git": False, "calls_github": False,
            "merges_pr": False, "runs_validation": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "POST_MERGE_ASSIMILATION_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.post_merge_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import PostMergeAssimilationReportBuilder

        return PostMergeAssimilationReportBuilder(self).write()
