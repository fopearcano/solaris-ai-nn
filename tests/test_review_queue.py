"""Review queue: item created, unresolved preserved, no task execution."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ReviewAssimilationQueue,
    ReviewQueueItem,
    ReviewQueueItemType,
    ReviewQueueStatus,
)


def test_queue_item_created():
    q = ReviewAssimilationQueue()
    q.add(ReviewQueueItem(item_type=ReviewQueueItemType.COLLECT_MISSING_ARTIFACT))
    assert q.to_dict()["review_queue_item_count"] == 1


def test_unresolved_item_preserved():
    q = ReviewAssimilationQueue()
    q.add(ReviewQueueItem(
        item_type=ReviewQueueItemType.ARCHIVE_UNRESOLVED_OBJECTION,
        status=ReviewQueueStatus.UNRESOLVED))
    assert q.to_dict()["open_queue_item_count"] == 1
    assert q.items[0].open is True


def test_completed_requires_evidence():
    # A "completed" item with no evidence ref is treated as still open.
    item = ReviewQueueItem(
        item_type=ReviewQueueItemType.UPDATE_CLAIM_REGISTRY,
        status=ReviewQueueStatus.COMPLETED)
    assert item.status == ReviewQueueStatus.OPEN
    # With explicit evidence, completion stands.
    item2 = ReviewQueueItem(
        item_type=ReviewQueueItemType.UPDATE_CLAIM_REGISTRY,
        status=ReviewQueueStatus.COMPLETED, evidence_ref="local:update_001")
    assert item2.status == ReviewQueueStatus.COMPLETED


def test_no_task_execution():
    q = ReviewAssimilationQueue()
    q.add(ReviewQueueItem(item_type=ReviewQueueItemType.RUN_FALSIFICATION))
    assert all(i["executed"] is False for i in q.to_dict()["items"])
