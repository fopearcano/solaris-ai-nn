"""Intake: research protocols exist; operator exposes merge rec + blockers."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog


def _runtime():
    rt = ImplementationIntakeRuntime(
        state_dir=".solaris_ai_nn_implementation_intake/opx")
    rt.load_manifest({
        "branch_spec": {"file_changes_expected": ["src/x.py"],
                        "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "added socket networking",
        "changed_file_list": ["src/x.py"],
        "patch_file": "+++ b/src/x.py\n+import socket\n",
        "test_results": {"by_category": {"safety": {"passed": True},
                                         "claim_guard": {"passed": True}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True}})
    rt.run()
    return rt


def test_research_protocols_exist():
    for name in ("implementation_intake_protocol", "diff_audit_protocol",
                 "spec_compliance_protocol", "test_result_audit_protocol",
                 "safety_regression_protocol", "merge_recommendation_protocol"):
        assert name in PROTOCOLS


def test_operator_catalog_exposes_intake():
    entries = [e for e in ProfileCatalog()._entries.values()
               if e.source_package == "implementation_intake"]
    assert entries


def test_operator_exposes_merge_recommendation_and_blockers():
    rt = _runtime()
    router = QueryRouter(components={"implementation_intake": rt})
    clf = OperatorInputClassifier()
    blocks = router.route_query(clf.classify("what blocks the merge?"))
    assert "blocker" in blocks.text.lower() or "merge" in blocks.text.lower()
    safety = router.route_query(clf.classify(
        "did it introduce a safety regression?"))
    assert "safety regression" in safety.text.lower()


def test_operator_safe_answers():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    merge = router.route_query(clf.classify("did Solaris merge the PR?"))
    assert "no." in merge.text.lower()
    assert "does not merge" in merge.text.lower()
    edit = router.route_query(clf.classify("did Solaris edit the code?"))
    assert "audit documents only" in edit.text.lower()
    ready = router.route_query(clf.classify(
        "is this implementation ready to merge?"))
    assert "advisory" in ready.text.lower()
