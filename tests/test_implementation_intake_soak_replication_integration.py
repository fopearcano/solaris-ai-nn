"""Post-merge validation includes mini soak / falsification / replication."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import (
    ImplementationIntakeRuntime,
    build_post_merge_plan,
)
from solaris_ai_nn.implementation_intake.post_merge_plan import PostMergeStageId


def test_post_merge_includes_soak_falsification_replication():
    ids = {s.stage_id for s in build_post_merge_plan().stages}
    assert PostMergeStageId.RUN_MINI_SOAK in ids
    assert PostMergeStageId.RUN_FALSIFICATION_REPLAY in ids
    assert PostMergeStageId.REGISTER_IN_REPLICATION in ids


def test_runtime_emits_post_merge_plan(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest({
        "branch_spec": {"file_changes_expected": ["src/x.py"],
                        "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "bounded change; does not prove life",
        "changed_file_list": ["src/x.py"],
        "patch_file": "+++ b/src/x.py\n+def f():\n+    return 1\n",
        "test_results": {"passed": 3, "failed": 0,
                         "by_category": {"safety": {"passed": True},
                                         "claim_guard": {"passed": True}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True}})
    rt.run()
    stage_ids = {s["stage_id"] for s in rt.post_merge["stages"]}
    assert PostMergeStageId.RUN_MINI_SOAK in stage_ids
    assert PostMergeStageId.REGISTER_IN_REPLICATION in stage_ids


def test_blocked_run_marks_plan_conditional(tmp_path):
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest({
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "import socket added",
        "changed_file_list": ["src/x.py"],
        "patch_file": "+++ b/src/x.py\n+import socket\n",
        "test_results": {"by_category": {"safety": {"passed": True},
                                         "claim_guard": {"passed": True}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True},
        "changed_file_list": ["src/x.py"]})
    rt.run()
    # Merge is blocked by safety; the post-merge plan is still produced but
    # conditional.
    assert rt.post_merge["conditional"] is True
