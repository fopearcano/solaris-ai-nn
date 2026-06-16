"""Review assimilation queue -- local next-cycle tasks; executes nothing.

:class:`ReviewAssimilationQueue` holds the next-cycle tasks derived from review
feedback (update claim registry / theory ledger / limitations / dossier / reviewer
pack, collect missing artifacts, rerun reproduction challenges, run ablation /
falsification / replication, revise metric, request operator decision, archive
unresolved objections, block public claim). The queue is local metadata; it
executes no task, preserves unresolved items, and completed items require explicit
local evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReviewQueueItemType:
    UPDATE_CLAIM_REGISTRY = "update_claim_registry"
    UPDATE_THEORY_LEDGER = "update_theory_ledger"
    UPDATE_LIMITATIONS = "update_limitations"
    UPDATE_PUBLICATION_DOSSIER = "update_publication_dossier"
    UPDATE_REVIEWER_PACK = "update_reviewer_pack"
    COLLECT_MISSING_ARTIFACT = "collect_missing_artifact"
    RERUN_REPRODUCTION_CHALLENGE = "rerun_reproduction_challenge"
    RUN_ABLATION = "run_ablation"
    RUN_FALSIFICATION = "run_falsification"
    RUN_REPLICATION = "run_replication"
    REVISE_METRIC = "revise_metric"
    REQUEST_OPERATOR_DECISION = "request_operator_decision"
    ARCHIVE_UNRESOLVED_OBJECTION = "archive_unresolved_objection"
    BLOCK_PUBLIC_CLAIM = "block_public_claim"
    UNKNOWN = "unknown"

    ALL = (UPDATE_CLAIM_REGISTRY, UPDATE_THEORY_LEDGER, UPDATE_LIMITATIONS,
           UPDATE_PUBLICATION_DOSSIER, UPDATE_REVIEWER_PACK,
           COLLECT_MISSING_ARTIFACT, RERUN_REPRODUCTION_CHALLENGE, RUN_ABLATION,
           RUN_FALSIFICATION, RUN_REPLICATION, REVISE_METRIC,
           REQUEST_OPERATOR_DECISION, ARCHIVE_UNRESOLVED_OBJECTION,
           BLOCK_PUBLIC_CLAIM, UNKNOWN)


class ReviewQueueStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    UNRESOLVED = "unresolved"
    ARCHIVED = "archived"

    ALL = (OPEN, IN_PROGRESS, COMPLETED, UNRESOLVED, ARCHIVED)
    PRESERVED = (UNRESOLVED, ARCHIVED)


class ReviewQueuePriority:
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    ALL = (URGENT, HIGH, MEDIUM, LOW)


@dataclass
class ReviewQueueItem:
    """One queue item (local metadata; executes nothing)."""

    item_type: str
    priority: str = ReviewQueuePriority.MEDIUM
    status: str = ReviewQueueStatus.OPEN
    refs: List[str] = field(default_factory=list)
    evidence_ref: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.item_type not in ReviewQueueItemType.ALL:
            self.item_type = ReviewQueueItemType.UNKNOWN
        if self.priority not in ReviewQueuePriority.ALL:
            self.priority = ReviewQueuePriority.MEDIUM
        if self.status not in ReviewQueueStatus.ALL:
            self.status = ReviewQueueStatus.OPEN
        # A "completed" item requires explicit local evidence; otherwise open.
        if self.status == ReviewQueueStatus.COMPLETED and not self.evidence_ref:
            self.status = ReviewQueueStatus.OPEN

    @property
    def open(self) -> bool:
        return self.status in (ReviewQueueStatus.OPEN,
                               ReviewQueueStatus.IN_PROGRESS,
                               ReviewQueueStatus.UNRESOLVED)

    def to_dict(self) -> Dict[str, Any]:
        return {"item_type": self.item_type, "priority": self.priority,
                "status": self.status, "refs": list(self.refs),
                "evidence_ref": self.evidence_ref, "detail": self.detail,
                "open": self.open, "executed": False}


@dataclass
class ReviewAssimilationQueue:
    """Holds review-assimilation queue items (local; no execution)."""

    items: List[ReviewQueueItem] = field(default_factory=list)

    def add(self, item: ReviewQueueItem) -> ReviewQueueItem:
        self.items.append(item)
        return item

    def open_items(self) -> List[ReviewQueueItem]:
        return [i for i in self.items if i.open]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_queue_item_count": len(self.items),
            "open_queue_item_count": len(self.open_items()),
            "items": [i.to_dict() for i in self.items],
            "note": "the queue is local metadata; it executes no task, preserves "
                    "unresolved items, and a completed item requires explicit "
                    "local evidence",
        }
