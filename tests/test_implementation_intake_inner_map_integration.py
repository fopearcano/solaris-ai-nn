"""Intake: Inner MAP includes implementation-intake state."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver


def _runtime(tmp_path):
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
    return rt


def test_inner_map_includes_intake(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(implementation_intake=rt).update()
    assert model.implementation_intake is not None
    assert model.implementation_intake["implementation_intake_enabled"] is True
    assert model.implementation_intake["modifies_source"] is False
    assert model.implementation_intake["merges_pr"] is False
    assert "implementation_intake" in model.to_dict()


def test_state_graph_has_intake_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ImplementationIntakeRuntime" in nodes
    assert "MergeRecommendation" in nodes
    assert "SafetyRegressionAudit" in nodes
