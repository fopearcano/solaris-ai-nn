"""Intake outputs are usable as future architecture evidence; reasons preserved."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime


def _blocked_runtime(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest({
        "branch_spec": {"file_changes_expected": ["src/x.py"],
                        "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "added socket networking; it is conscious",
        "changed_file_list": ["src/x.py", ".github/workflows/ci.yml"],
        "patch_file": "+++ b/src/x.py\n+import socket\n",
        "test_results": {"passed": 1, "failed": 2,
                         "by_category": {"unit": {"passed": 1, "failed": 2}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True}})
    rt.run()
    return rt


def test_outputs_usable_as_architecture_evidence(tmp_path):
    rt = _blocked_runtime(tmp_path)
    evidence = rt.architecture_evidence()
    assert "merge_recommendation" in evidence
    assert "spec_compliance_counts" in evidence
    assert "post_merge_validation_plan" in evidence
    assert "safety_regression_findings" in evidence


def test_blocked_implementation_reason_preserved(tmp_path):
    rt = _blocked_runtime(tmp_path)
    evidence = rt.architecture_evidence()
    # The blocking reason(s) are preserved for future architecture revision.
    assert evidence["blocked_implementation_reason"]
    assert "safety" in evidence["blocked_implementation_reason"]


def test_missing_evidence_listed(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest({"implementation_summary": "x"})  # most required missing
    rt.run()
    evidence = rt.architecture_evidence()
    assert evidence["missing_evidence"]  # critical missing artifacts preserved
