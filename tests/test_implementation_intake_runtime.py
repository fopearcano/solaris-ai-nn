"""Intake runtime: bounded, documents only, no source/GitHub/Git/PR/agent."""

from __future__ import annotations

import inspect

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime
from solaris_ai_nn.implementation_intake import intake_runtime


def _bundle():
    return {
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
        "safety_invariant_results": {"passed": True}}


def test_bounded_runtime(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest(_bundle())
    out = rt.run()
    assert out["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_manifest(_bundle())
    assert rt.run()["refused"] is True


def test_documents_generated(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest(_bundle())
    rt.run()
    out = rt.write_artifacts()
    import os
    assert os.path.isfile(out["markdown"])
    assert len(out["documents"]) >= 11


def test_status_disclaims_mutation(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest(_bundle())
    rt.run()
    st = rt.intake_status()
    assert st["modifies_source"] is False
    assert st["merges_pr"] is False
    assert st["calls_github"] is False
    assert st["runs_external_agent"] is False


def test_no_source_github_git_pr_agent_in_source():
    src = inspect.getsource(intake_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "gh pr" not in src
    assert "git checkout" not in src
    assert "github api" not in src.lower()
