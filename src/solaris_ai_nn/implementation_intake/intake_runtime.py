"""Implementation intake runtime -- the bounded, read-only evidence auditor.

:class:`ImplementationIntakeRuntime` loads an intake manifest of local
artifacts, reads them, runs the diff/spec/test/safety/ClaimGuard audits, builds
the coverage matrix, and generates the advisory merge recommendation, rollback
recommendation, and post-merge validation plan -- writing documents only. It
modifies no source, executes no merge, creates/approves no PR, calls no GitHub,
runs no Git, runs no external coding agent, runs no shell/network/browser/OS, and
never approves itself.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .artifact_reader import ImplementationArtifactReader
from .claimguard_audit import ClaimGuardAudit
from .coverage_matrix import build_coverage_matrix
from .diff_audit import DiffAudit
from .intake_manifest import ImplementationIntakeManifest
from .merge_recommendation import MergeRecommendationBuilder
from .post_merge_plan import build_post_merge_plan
from .rollback_recommendation import RollbackRecommendationBuilder
from .safety import ImplementationIntakeSafetyValidator
from .safety_regression import SafetyRegressionAudit
from .spec_compliance import SpecComplianceAudit
from .test_result_audit import TestResultAudit


@dataclass
class ImplementationIntakeRuntime:
    """Bounded read-only auditor: implementation evidence -> advisory reports."""

    state_dir: str = ".solaris_ai_nn_implementation_intake"
    intake_manifest_path: Optional[str] = None
    max_runtime_s: float = 30.0
    report_only: bool = True
    dry_run: bool = False
    require_all_safety_gates: bool = True
    require_test_results: bool = True
    require_claimguard_results: bool = True

    manifest: ImplementationIntakeManifest = field(default=None, init=False)
    reader: ImplementationArtifactReader = field(
        default_factory=ImplementationArtifactReader, init=False)
    safety: ImplementationIntakeSafetyValidator = field(
        default_factory=ImplementationIntakeSafetyValidator, init=False)

    diff_audit: Dict[str, Any] = field(default_factory=dict, init=False)
    spec_compliance: Dict[str, Any] = field(default_factory=dict, init=False)
    test_audit: Dict[str, Any] = field(default_factory=dict, init=False)
    safety_regression: Dict[str, Any] = field(default_factory=dict, init=False)
    claimguard_audit: Dict[str, Any] = field(default_factory=dict, init=False)
    coverage: Dict[str, Any] = field(default_factory=dict, init=False)
    merge: Dict[str, Any] = field(default_factory=dict, init=False)
    rollback: Dict[str, Any] = field(default_factory=dict, init=False)
    post_merge: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.manifest = ImplementationIntakeManifest()
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    # -- input --------------------------------------------------------------

    def load_manifest(self, bundle: Optional[Dict[str, Any]] = None,
                      ) -> ImplementationIntakeManifest:
        """Provide implementation artifacts (in-memory bundle keyed by id)."""
        for aid, payload in (bundle or {}).items():
            if payload is None:
                continue
            result = self.reader.read_payload(aid, payload)
            from .intake_manifest import ImplementationArtifactStatus

            status = (ImplementationArtifactStatus.PROVIDED if result.ok
                      else ImplementationArtifactStatus.EMPTY
                      if result.issue and result.issue.kind == "empty"
                      else ImplementationArtifactStatus.CORRUPT
                      if result.issue and result.issue.kind == "corrupt"
                      else ImplementationArtifactStatus.PROVIDED)
            self.manifest.provide(aid, payload, status=status,
                                  detail=result.kind)
        return self.manifest

    # -- reference spec (from compiler artifacts) ----------------------------

    def _reference_spec(self) -> Dict[str, Any]:
        """Merge compiler artifacts into a comparable spec requirement set."""
        branch = self.manifest.get("branch_spec") or {}
        prompt = self.manifest.get("implementation_prompt") or {}
        sections = prompt.get("sections", {}) if isinstance(prompt, dict) else {}
        return {
            "proposed_changes": (branch.get("file_changes_expected")
                                 or sections.get("target_files") or []),
            "expected_behavior": sections.get("required_classes_functions", []),
            "tests_required": (branch.get("tests_required")
                               or sections.get("tests") or []),
            "examples_required": sections.get("examples", []),
            "docs_required": (branch.get("docs_required")
                              or sections.get("docs_updates") or []),
            "safety_gates": (branch.get("safety_checks")
                             or self._safety_gate_ids()),
        }

    def _safety_gate_ids(self) -> List[str]:
        gates = self.manifest.get("safety_gates") or {}
        if isinstance(gates, dict):
            results = gates.get("results") or gates.get("summary", {}).get(
                "results", [])
            return [r.get("gate_type") for r in results if isinstance(r, dict)]
        return []

    def _expected_files(self) -> List[str]:
        branch = self.manifest.get("branch_spec") or {}
        ref = self._reference_spec()
        return list(branch.get("file_changes_expected", [])) + \
            list(ref.get("tests_required", [])) + \
            list(ref.get("docs_required", []))

    def _generated_documents(self) -> Dict[str, str]:
        """Collect generated Markdown/doc text supplied for ClaimGuard scan."""
        docs: Dict[str, str] = {}
        summary = self.manifest.get("implementation_summary")
        if isinstance(summary, str):
            docs["implementation_summary"] = summary
        cg = self.manifest.get("claimguard_results")
        if isinstance(cg, dict) and isinstance(cg.get("documents"), dict):
            docs.update(cg["documents"])
        for key in ("diff_summary",):
            val = self.manifest.get(key)
            if isinstance(val, str):
                docs[key] = val
        return docs

    # -- audit pipeline -----------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}

        changed_files = self.manifest.get("changed_file_list") or \
            self.manifest.get("diff_summary") or []
        if isinstance(changed_files, dict):
            changed_files = changed_files.get("changed_files", [])
        patch_text = self.manifest.get("patch_file") or ""
        if isinstance(patch_text, dict):
            patch_text = patch_text.get("patch", "")
        ref_spec = self._reference_spec()

        self.diff_audit = DiffAudit().audit(
            changed_files=changed_files, expected_files=self._expected_files(),
            required_files=ref_spec.get("tests_required", []),
            patch_text=str(patch_text))

        self.spec_compliance = SpecComplianceAudit().audit(
            spec=ref_spec, changed_files=changed_files,
            test_results=self.manifest.get("test_results"),
            example_results=self.manifest.get("example_results"))

        self.test_audit = TestResultAudit().audit(
            test_results=self.manifest.get("test_results"))

        self.safety_regression = SafetyRegressionAudit().audit(
            patch_text=str(patch_text),
            implementation_summary=str(
                self.manifest.get("implementation_summary") or ""))

        self.claimguard_audit = ClaimGuardAudit().audit(
            documents=self._generated_documents(),
            claimguard_results=self.manifest.get("claimguard_results"))

        self.coverage = build_coverage_matrix(
            spec_compliance=self.spec_compliance, diff_audit=self.diff_audit,
            test_audit=self.test_audit).to_dict()

        self.merge = MergeRecommendationBuilder().build(
            manifest=self.manifest.to_dict(), diff_audit=self.diff_audit,
            spec_compliance=self.spec_compliance, test_audit=self.test_audit,
            safety_regression=self.safety_regression,
            claimguard_audit=self.claimguard_audit,
            coverage_matrix=self.coverage).to_dict()

        self.rollback = RollbackRecommendationBuilder().build(
            merge_recommendation=self.merge,
            safety_regression=self.safety_regression, test_audit=self.test_audit,
            spec_compliance=self.spec_compliance, diff_audit=self.diff_audit,
            claimguard_audit=self.claimguard_audit,
            manifest=self.manifest.to_dict()).to_dict()

        blocked = self.merge["status"] in (
            "block_merge_due_to_safety", "block_merge_due_to_tests",
            "block_merge_due_to_spec_noncompliance",
            "block_merge_due_to_missing_evidence")
        self.post_merge = build_post_merge_plan(conditional=blocked).to_dict()
        return {"refused": False, "merge_status": self.merge["status"]}

    # -- integration views --------------------------------------------------

    def architecture_evidence(self) -> Dict[str, Any]:
        """Outputs usable as future architecture-evolution evidence."""
        return {
            "merge_recommendation": self.merge.get("status"),
            "spec_compliance_counts": self.spec_compliance.get("counts"),
            "blocked_implementation_reason": [
                b["kind"] for b in self.merge.get("blockers", [])],
            "safety_regression_findings": self.safety_regression.get(
                "findings", []),
            "missing_evidence": self.manifest.blockers(),
            "post_merge_validation_plan": self.post_merge.get("stages", []),
        }

    def intake_status(self) -> Dict[str, Any]:
        return {
            "implementation_intake_enabled": True,
            "implementation_artifact_count": self.manifest.to_dict()[
                "present_count"],
            "missing_artifact_count": len(self.manifest.warnings())
            + len(self.manifest.blockers()),
            "corrupt_artifact_count": sum(
                1 for i in self.reader.issues if i.kind == "corrupt"),
            "diff_finding_count": len(self.diff_audit.get("findings", [])),
            "unexpected_file_change_count": self.diff_audit.get(
                "unexpected_file_change_count", 0),
            "forbidden_file_change_count": self.diff_audit.get(
                "forbidden_file_change_count", 0),
            "spec_satisfied_count": self.spec_compliance.get(
                "spec_satisfied_count", 0),
            "spec_unsatisfied_count": self.spec_compliance.get(
                "spec_unsatisfied_count", 0),
            "spec_compliance_status": self._spec_status(),
            "test_failure_count": self.test_audit.get("test_failure_count", 0),
            "missing_required_test_count": self.test_audit.get(
                "missing_required_test_count", 0),
            "safety_regression_count": self.safety_regression.get(
                "finding_count", 0),
            "critical_safety_regression_count": self.safety_regression.get(
                "critical_count", 0),
            "claimguard_finding_count": self.claimguard_audit.get(
                "finding_count", 0),
            "coverage_gap_count": self.coverage.get("coverage_gap_count", 0),
            "merge_recommendation_status": self.merge.get("status"),
            "merge_blocker_count": self.merge.get("blocker_count", 0),
            "rollback_recommendation_status": (
                "recommended" if self.rollback.get("recommended")
                else "not_recommended"),
            "rollback_trigger_count": len(self.rollback.get("reasons", [])),
            "latest_intake_report_path": self._report_path(),
            "modifies_source": False, "merges_pr": False, "calls_github": False,
            "runs_external_agent": False,
        }

    def _spec_status(self) -> str:
        if self.spec_compliance.get("blocking_failure_count", 0):
            return "blocked"
        counts = self.spec_compliance.get("counts", {}) or {}
        if counts.get("not_satisfied") or counts.get("unknown"):
            return "partially_satisfied"
        if counts.get("satisfied"):
            return "satisfied"
        return "unknown"

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "IMPLEMENTATION_INTAKE_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.intake_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ImplementationIntakeReportBuilder

        return ImplementationIntakeReportBuilder(self).write()
