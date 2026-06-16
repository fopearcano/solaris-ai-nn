"""Post-merge: research protocols exist; operator exposes baseline/rollback."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog
from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def _runtime():
    rt = PostMergeAssimilationRuntime(
        state_dir=".solaris_ai_nn_post_merge/opx", candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle({
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": {"merge_recommendation_status":
                                  "block_merge_due_to_safety",
                                  "critical_safety_regression_count": 2,
                                  "forbidden_file_change_count": 1},
        "validation_results": {"full_test_run": {"passed": False}},
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": {"safety_regression_status": True}})
    rt.run()
    return rt


def test_research_protocols_exist():
    for name in ("post_merge_assimilation_protocol",
                 "baseline_registry_protocol", "baseline_comparison_protocol",
                 "regression_watch_protocol", "module_status_update_protocol",
                 "rollback_watch_protocol", "followup_queue_protocol"):
        assert name in PROTOCOLS


def test_operator_catalog_exposes_post_merge():
    entries = [e for e in ProfileCatalog()._entries.values()
               if e.source_package == "post_merge_assimilation"]
    assert entries


def test_operator_exposes_baseline_regression_rollback():
    rt = _runtime()
    router = QueryRouter(components={"post_merge_assimilation": rt})
    clf = OperatorInputClassifier()
    baseline = router.route_query(clf.classify("what is the current baseline?"))
    assert "baseline" in baseline.text.lower()
    regress = router.route_query(clf.classify("did the new baseline regress?"))
    assert "regression" in regress.text.lower()
    rollback = router.route_query(clf.classify("should I rollback?"))
    assert "rollback" in rollback.text.lower()


def test_operator_safe_answers():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    merge = router.route_query(clf.classify("did Solaris merge this?"))
    assert "no." in merge.text.lower()
    assert "did not merge" in merge.text.lower()
    git = router.route_query(clf.classify("did Solaris run Git?"))
    assert "does not run git" in git.text.lower()
