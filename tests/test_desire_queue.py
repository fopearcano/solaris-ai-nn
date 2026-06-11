"""Tests for the DesireQueue."""

from __future__ import annotations

import time

from solaris_ai_nn.executive.desire_queue import DesirePriority, DesireQueue
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _candidate(proposal, motivation=0.5, blocked=False):
    return DesireCandidate(proposal=proposal, motivation=motivation,
                           confidence=0.6, blocked=blocked,
                           blocked_reason="test block" if blocked else "")


def test_push_pop_deterministic():
    a = DesireQueue()
    b = DesireQueue()
    candidates = [_candidate("look", 0.4), _candidate("avoid_danger", 0.4),
                  _candidate("rest", 0.4)]
    a.push_many(candidates)
    b.push_many(candidates)
    assert [i.proposal for i in a.peek()] == [i.proposal for i in b.peek()]
    # avoid_danger carries structural HIGH priority: it pops first.
    assert a.pop_next().proposal == "avoid_danger"
    assert a.pop_next().proposal in ("rest", "look")


def test_expired_desires_removed():
    queue = DesireQueue()
    queue.push(_candidate("look"), ttl_s=0.01)
    queue.push(_candidate("rest"), ttl_s=60.0)
    time.sleep(0.05)
    assert queue.remove_expired() == 1
    assert [i.proposal for i in queue.items] == ["rest"]
    # Expired desires never become suggestions via pop either.
    queue.push(_candidate("look"), ttl_s=0.01)
    time.sleep(0.05)
    popped = queue.pop_next()
    assert popped.proposal == "rest"
    assert queue.expired_total >= 2


def test_inhibited_desires_preserved():
    queue = DesireQueue()
    queued = queue.push(_candidate("explore_safely"))
    queue.mark_inhibited(queued.desire_id, "safety beats curiosity")
    assert queue.pop_next() is None  # nothing live
    # But the inhibited entry is still visible for explanation.
    snap = queue.snapshot()
    assert snap["inhibited"][0]["proposal"] == "explore_safely"
    assert snap["inhibited"][0]["reason"] == "safety beats curiosity"
    # Pre-blocked candidates arrive inhibited with their reason.
    queue.push(_candidate("approach_reward", blocked=True))
    assert any(i["proposal"] == "approach_reward"
               for i in queue.snapshot()["inhibited"])


def test_one_live_entry_per_proposal():
    queue = DesireQueue()
    queue.push(_candidate("rest", 0.3))
    queue.push(_candidate("rest", 0.9))
    assert len(queue) == 1
    assert queue.peek()[0].urgency == 0.9


def test_priorities():
    assert DesirePriority.PROPOSAL_PRIORITY["safe_shutdown_recommended"] \
        == DesirePriority.CRITICAL
    assert DesirePriority.PROPOSAL_PRIORITY["explore_safely"] \
        == DesirePriority.LOW
