"""Follow-up queue: items queued, executes nothing, statuses serialize."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    FollowupItemType,
    FollowupStatus,
    PostMergeFollowupQueue,
    build_followup_queue,
)


def test_followup_items_queued_for_missing_validation():
    queue = build_followup_queue(
        validation={"missing_required": ["full_test_run",
                                         "safety_invariant_run"]},
        regression={"baseline_regression_count": 0}, module_status={},
        rollback={"recommendation": "monitor"},
        baseline_validated=False).to_dict()
    types = {i["item_type"] for i in queue["items"]}
    assert FollowupItemType.RERUN_TESTS in types
    assert FollowupItemType.RUN_SAFETY_INVARIANTS in types


def test_validated_baseline_queues_soak_and_replication():
    queue = build_followup_queue(
        validation={"missing_required": []},
        regression={"baseline_regression_count": 0}, module_status={},
        rollback={"recommendation": "no_rollback_needed"},
        baseline_validated=True).to_dict()
    types = {i["item_type"] for i in queue["items"]}
    assert FollowupItemType.RUN_MINI_SOAK in types
    assert FollowupItemType.REGISTER_REPLICATION_RUN in types
    assert FollowupItemType.RUN_FALSIFICATION_REPLAY in types


def test_queue_does_not_execute():
    queue = build_followup_queue(
        validation={"missing_required": []}, regression={}, module_status={},
        rollback={"recommendation": "no_rollback_needed"},
        baseline_validated=True).to_dict()
    assert queue["executes_tasks"] is False
    assert queue["calls_external_tools"] is False
    assert all(i["executed"] is False for i in queue["items"])


def test_statuses_serialize():
    q = PostMergeFollowupQueue()
    q.add(FollowupItemType.REQUEST_OPERATOR_REVIEW,
          status=FollowupStatus.OPERATOR_PENDING)
    d = q.to_dict()
    assert d["items"][0]["status"] == FollowupStatus.OPERATOR_PENDING


def test_unknown_item_type_ignored():
    q = PostMergeFollowupQueue()
    q.add("not_a_real_item")
    assert q.to_dict()["followup_item_count"] == 0
