"""Post-merge: validated -> soak/replication follow-up; blocked -> rollback."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime
from solaris_ai_nn.post_merge_assimilation import FollowupItemType


def _runtime(tmp_path, blocked=False):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    if blocked:
        intake = {"merge_recommendation_status": "block_merge_due_to_safety",
                  "critical_safety_regression_count": 2,
                  "forbidden_file_change_count": 1}
        validation = {"full_test_run": {"passed": False}}
        candidate = {"safety_regression_status": True}
    else:
        intake = {"merge_recommendation_status": "recommend_merge",
                  "critical_safety_regression_count": 0,
                  "spec_compliance_status": "satisfied", "test_failure_count": 0}
        validation = {"full_test_run": {"passed": True},
                      "safety_invariant_run": {"passed": True},
                      "claimguard_run": {"safe": True},
                      "mini_soak": {"passed": True}}
        candidate = {"sensorium_metrics": 0.6}
    rt.load_bundle({
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": intake, "validation_results": validation,
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": candidate})
    rt.run()
    return rt


def test_validated_baseline_recommends_soak_and_replication(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.candidate.status in ("validated", "validated_with_warnings")
    types = {i["item_type"] for i in rt.followup["items"]}
    assert FollowupItemType.RUN_MINI_SOAK in types
    assert FollowupItemType.REGISTER_REPLICATION_RUN in types
    assert FollowupItemType.RUN_FALSIFICATION_REPLAY in types


def test_blocked_baseline_recommends_rollback_or_revision(tmp_path):
    rt = _runtime(tmp_path, blocked=True)
    assert rt.candidate.blocked or rt.candidate.status == "rollback_recommended"
    assert rt.rollback["recommendation"] in (
        "rollback_recommended", "request_revision", "immediate_operator_review",
        "block_baseline")
    types = {i["item_type"] for i in rt.followup["items"]}
    assert (FollowupItemType.REQUEST_REVISION_PROMPT in types
            or FollowupItemType.REQUEST_OPERATOR_REVIEW in types)
