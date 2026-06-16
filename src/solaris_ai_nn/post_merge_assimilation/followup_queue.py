"""Post-merge follow-up queue -- local metadata; executes nothing.

:class:`PostMergeFollowupQueue` records the follow-up work a candidate baseline
needs (rerun tests, run safety invariants / ClaimGuard / examples, short fixture
demo, mini soak, falsification replay, register replication run, update
architecture evidence, request operator review / revision prompt, monitor
regression, archive baseline). It is local metadata: it executes no task, calls
no external tool, and modifies no source.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class FollowupItemType:
    RERUN_TESTS = "rerun_tests"
    RUN_SAFETY_INVARIANTS = "run_safety_invariants"
    RUN_CLAIMGUARD = "run_ClaimGuard"
    RUN_EXAMPLES = "run_examples"
    RUN_SHORT_FIXTURE_DEMO = "run_short_fixture_demo"
    RUN_MINI_SOAK = "run_mini_soak"
    RUN_FALSIFICATION_REPLAY = "run_falsification_replay"
    REGISTER_REPLICATION_RUN = "register_replication_run"
    UPDATE_ARCHITECTURE_EVIDENCE = "update_architecture_evidence"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    REQUEST_REVISION_PROMPT = "request_revision_prompt"
    MONITOR_REGRESSION = "monitor_regression"
    ARCHIVE_BASELINE = "archive_baseline"

    ALL = (RERUN_TESTS, RUN_SAFETY_INVARIANTS, RUN_CLAIMGUARD, RUN_EXAMPLES,
           RUN_SHORT_FIXTURE_DEMO, RUN_MINI_SOAK, RUN_FALSIFICATION_REPLAY,
           REGISTER_REPLICATION_RUN, UPDATE_ARCHITECTURE_EVIDENCE,
           REQUEST_OPERATOR_REVIEW, REQUEST_REVISION_PROMPT,
           MONITOR_REGRESSION, ARCHIVE_BASELINE)


class FollowupPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    ALL = (LOW, MEDIUM, HIGH, URGENT)


class FollowupStatus:
    QUEUED = "queued"
    OPERATOR_PENDING = "operator_pending"
    DEFERRED = "deferred"

    ALL = (QUEUED, OPERATOR_PENDING, DEFERRED)


@dataclass
class FollowupItem:
    """One queued follow-up task (metadata only; never executed)."""

    item_type: str
    priority: str = FollowupPriority.MEDIUM
    status: str = FollowupStatus.QUEUED
    detail: str = ""
    created_ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"item_type": self.item_type, "priority": self.priority,
                "status": self.status, "detail": self.detail,
                "executed": False, "created_ts": self.created_ts}


@dataclass
class PostMergeFollowupQueue:
    """A local metadata queue of post-merge follow-up tasks (executes nothing)."""

    items: List[FollowupItem] = field(default_factory=list)

    def add(self, item_type: str, *, priority: str = FollowupPriority.MEDIUM,
            status: str = FollowupStatus.QUEUED, detail: str = "") -> None:
        if item_type not in FollowupItemType.ALL:
            return
        self.items.append(FollowupItem(item_type=item_type, priority=priority,
                                       status=status, detail=detail))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "followup_item_count": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "executes_tasks": False, "calls_external_tools": False,
            "modifies_source": False,
            "note": "local metadata queue; it executes no task, calls no "
                    "external tool, and modifies no source",
        }


def build_followup_queue(*, validation: Dict[str, Any],
                         regression: Dict[str, Any],
                         module_status: Dict[str, Any],
                         rollback: Dict[str, Any],
                         baseline_validated: bool) -> PostMergeFollowupQueue:
    """Build the follow-up queue from the post-merge evidence."""
    queue = PostMergeFollowupQueue()
    validation = validation or {}
    regression = regression or {}
    rollback = rollback or {}

    # Missing validation artifacts -> queue the matching reruns.
    missing = set(validation.get("missing_required", []))
    if "full_test_run" in missing:
        queue.add(FollowupItemType.RERUN_TESTS, priority=FollowupPriority.HIGH,
                  detail="full test run evidence missing")
    if "safety_invariant_run" in missing:
        queue.add(FollowupItemType.RUN_SAFETY_INVARIANTS,
                  priority=FollowupPriority.URGENT,
                  detail="safety invariant evidence missing")
    if "claimguard_run" in missing:
        queue.add(FollowupItemType.RUN_CLAIMGUARD,
                  priority=FollowupPriority.HIGH,
                  detail="ClaimGuard evidence missing")

    # Critical/major regressions -> review / revision / monitoring.
    rec = rollback.get("recommendation")
    if rec == "rollback_recommended":
        queue.add(FollowupItemType.REQUEST_OPERATOR_REVIEW,
                  priority=FollowupPriority.URGENT,
                  status=FollowupStatus.OPERATOR_PENDING,
                  detail="rollback recommended")
        queue.add(FollowupItemType.REQUEST_REVISION_PROMPT,
                  priority=FollowupPriority.HIGH,
                  detail="re-compile a revision prompt for the experiment")
    elif rec == "request_revision":
        queue.add(FollowupItemType.REQUEST_REVISION_PROMPT,
                  priority=FollowupPriority.HIGH)
    if regression.get("baseline_regression_count", 0) > 0:
        queue.add(FollowupItemType.MONITOR_REGRESSION,
                  detail="watch the regressed dimension(s) on the next baseline")

    # Validated baselines -> soak / falsification / replication follow-ups.
    if baseline_validated:
        queue.add(FollowupItemType.RUN_SHORT_FIXTURE_DEMO,
                  priority=FollowupPriority.LOW)
        queue.add(FollowupItemType.RUN_MINI_SOAK)
        queue.add(FollowupItemType.RUN_FALSIFICATION_REPLAY)
        queue.add(FollowupItemType.REGISTER_REPLICATION_RUN)
        queue.add(FollowupItemType.UPDATE_ARCHITECTURE_EVIDENCE,
                  priority=FollowupPriority.LOW)
    return queue
