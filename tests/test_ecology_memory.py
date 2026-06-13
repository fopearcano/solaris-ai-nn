"""Tests for bounded ecology memory."""

from __future__ import annotations

from solaris_ai_nn.ecology.ecology_memory import (
    EcologyEpisode,
    EcologyMemory,
)
from solaris_ai_nn.ecology.events import EcologyEventType


def test_event_counts_accumulate():
    memory = EcologyMemory()
    memory.record_event(EcologyEventType.REGULAR_SIGNAL)
    memory.record_event(EcologyEventType.REGULAR_SIGNAL)
    memory.record_event(EcologyEventType.ANOMALY)
    assert memory.event_counts["regular_signal"] == 2
    assert memory.total_events() == 3


def test_window_records_are_bounded():
    memory = EcologyMemory(max_window_records=10)
    for i in range(50):
        memory.record_window("anomaly", {"step": i})
    assert len(memory.anomaly_windows) == 10


def test_episodes_are_bounded():
    memory = EcologyMemory(max_episodes=5)
    for i in range(20):
        memory.record_episode(EcologyEpisode(step_start=i, step_end=i + 1))
    assert len(memory.episodes) == 5


def test_over_budget_false_under_caps():
    memory = EcologyMemory()
    memory.record_episode(EcologyEpisode(step_start=0))
    assert memory.over_budget is False


def test_unknown_window_kind_ignored():
    memory = EcologyMemory()
    memory.record_window("not_a_real_bucket", {"x": 1})
    assert memory.snapshot()["anomaly_windows"] == 0


def test_snapshot_shape():
    memory = EcologyMemory()
    memory.record_event(EcologyEventType.NOVEL_SIGNAL)
    memory.record_regime(0, "mixed_nursery")
    snap = memory.snapshot()
    assert snap["total_events"] == 1
    assert "event_counts" in snap
    assert "regime_changes" in snap
