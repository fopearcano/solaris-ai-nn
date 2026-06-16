"""Intake reports: all reports generated, ClaimGuard-scanned, advisory note."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime


def _runtime(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest({
        "branch_spec": {"file_changes_expected": ["src/x.py"],
                        "tests_required": ["tests/test_x.py"],
                        "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "bounded change; does not prove life",
        "changed_file_list": ["src/x.py", "tests/test_x.py"],
        "patch_file": "+++ b/src/x.py\n+def f():\n+    return 1\n",
        "test_results": {"passed": 5, "failed": 0,
                         "by_category": {"safety": {"passed": True},
                                         "claim_guard": {"passed": True}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True}})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("IMPLEMENTATION_INTAKE_REPORT.md",
                     "IMPLEMENTATION_INTAKE_REPORT.json", "DIFF_AUDIT.md",
                     "SPEC_COMPLIANCE.md", "TEST_RESULT_AUDIT.md",
                     "SAFETY_REGRESSION_AUDIT.md", "CLAIMGUARD_AUDIT.md",
                     "COVERAGE_MATRIX.md", "MERGE_RECOMMENDATION.md",
                     "ROLLBACK_RECOMMENDATION.md",
                     "POST_MERGE_VALIDATION_PLAN.md"):
        assert expected in names


def test_claim_guard_scans_reports(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_advisory_disclaimer_present(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    proofs = " ".join(data["sections"]["what_this_does_not_do"]).lower()
    assert "no source code was modified" in proofs
    assert "no pull request was merged" in proofs
    assert "advisory audit only" in proofs
