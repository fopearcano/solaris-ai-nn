"""DesireQueue -- competing Desire candidates, deterministically ordered.

Candidates from the homeostasis layer enter as :class:`QueuedDesire` rows
with priority/urgency/confidence and full provenance. Expired desires can
never become action suggestions; inhibited desires stay in the queue,
visible, with their reasons -- audit before tidiness.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DesirePriority:
    CRITICAL = 1.0
    HIGH = 0.75
    NORMAL = 0.5
    LOW = 0.25

    # Proposals with structural priority (safety/continuity first).
    PROPOSAL_PRIORITY = {
        "safe_shutdown_recommended": CRITICAL,
        "request_operator_review": CRITICAL,
        "avoid_danger": HIGH,
        "checkpoint_now": HIGH,
        "remain_observe_only": HIGH,
        "rest": NORMAL,
        "stabilize": NORMAL,
        "reduce_activity": NORMAL,
        "consolidate_memory": NORMAL,
        "seek_signal": LOW,
        "look": LOW,
        "run_replay": LOW,
        "explore_safely": LOW,
        "approach_reward": LOW,
    }


@dataclass
class QueuedDesire:
    """One queued Desire candidate with provenance and lifecycle flags."""

    proposal: str
    candidate: Any = None  # the Prompt-16 DesireCandidate (kept whole)
    priority: float = DesirePriority.NORMAL
    urgency: float = 0.0
    confidence: float = 0.5
    source_needs: List[str] = field(default_factory=list)
    source_drives: List[str] = field(default_factory=list)
    source_context: str = ""
    safety_status: str = "ok"
    governance_status: str = "ok"
    inhibited: bool = False
    inhibition_reason: str = ""
    expires_at: Optional[float] = None
    desire_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, now: Optional[float] = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at

    def sort_key(self) -> tuple:
        """Deterministic: priority, urgency, confidence, then proposal."""
        return (-self.priority, -self.urgency, -self.confidence,
                self.proposal, self.desire_id)

    def to_dict(self) -> Dict[str, Any]:
        data = dict(self.__dict__)
        data["candidate"] = (self.candidate.to_dict()
                             if hasattr(self.candidate, "to_dict")
                             else None)
        return data


@dataclass
class DesireQueue:
    """Deterministically ordered queue of Desire candidates."""

    max_size: int = 50
    items: List[QueuedDesire] = field(default_factory=list)
    expired_total: int = field(default=0, init=False)
    inhibited_total: int = field(default=0, init=False)

    def push(self, candidate: Any,
             ttl_s: Optional[float] = 60.0) -> QueuedDesire:
        """Queue one Prompt-16 DesireCandidate (or proposal string)."""
        proposal = getattr(candidate, "proposal", str(candidate))
        queued = QueuedDesire(
            proposal=proposal, candidate=candidate,
            priority=DesirePriority.PROPOSAL_PRIORITY.get(
                proposal, DesirePriority.NORMAL),
            urgency=float(getattr(candidate, "motivation", 0.0) or 0.0),
            confidence=float(getattr(candidate, "confidence", 0.5) or 0.5),
            source_needs=list(getattr(candidate, "source_needs", [])),
            source_drives=list(getattr(candidate, "source_drives", [])),
            inhibited=bool(getattr(candidate, "blocked", False)),
            inhibition_reason=str(getattr(candidate, "blocked_reason", "")),
            expires_at=(time.time() + ttl_s if ttl_s is not None else None))
        if queued.inhibited:
            self.inhibited_total += 1
        # One live entry per proposal: the newer push replaces the older.
        self.items = [i for i in self.items if i.proposal != proposal]
        self.items.append(queued)
        self.items.sort(key=lambda i: i.sort_key())
        self.items = self.items[:self.max_size]
        return queued

    def push_many(self, candidates: List[Any],
                  ttl_s: Optional[float] = 60.0) -> List[QueuedDesire]:
        return [self.push(c, ttl_s=ttl_s) for c in candidates]

    def peek(self, limit: int = 10) -> List[QueuedDesire]:
        """The next candidates in order (expired excluded, inhibited kept)."""
        now = time.time()
        return [i for i in self.items if not i.is_expired(now)][:limit]

    def pop_next(self) -> Optional[QueuedDesire]:
        """The best live, non-inhibited desire (removed from the queue)."""
        self.remove_expired()
        for index, item in enumerate(self.items):
            if not item.inhibited:
                return self.items.pop(index)
        return None

    def mark_inhibited(self, desire_id: str, reason: str,
                       ) -> Optional[QueuedDesire]:
        for item in self.items:
            if item.desire_id == desire_id:
                if not item.inhibited:
                    self.inhibited_total += 1
                item.inhibited = True
                item.inhibition_reason = reason
                return item
        return None

    def remove_expired(self, now: Optional[float] = None) -> int:
        before = len(self.items)
        self.items = [i for i in self.items if not i.is_expired(now)]
        removed = before - len(self.items)
        self.expired_total += removed
        return removed

    def __len__(self) -> int:
        return len(self.items)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "length": len(self.items),
            "live": [i.proposal for i in self.items if not i.inhibited][:10],
            "inhibited": [{"proposal": i.proposal,
                           "reason": i.inhibition_reason}
                          for i in self.items if i.inhibited][:10],
            "expired_total": self.expired_total,
            "inhibited_total": self.inhibited_total,
        }
