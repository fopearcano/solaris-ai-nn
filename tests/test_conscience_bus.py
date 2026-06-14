"""Conscience bus: publish/subscribe, JSONL logging, deterministic replay."""

from __future__ import annotations

import pytest

from solaris_ai_nn.conscience import BusTopic, ConscienceBus


def test_publish_increments_and_traces(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path))
    bus.publish(BusTopic.STIMULUS, "src", {"x": 1}, step=0)
    bus.publish(BusTopic.PUSH, "src", {"y": 2}, step=0)
    assert bus.message_count() == 2
    assert bus.trace.counts[BusTopic.STIMULUS] == 1


def test_unknown_topic_rejected(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path))
    with pytest.raises(ValueError):
        bus.publish("not_a_topic", "src", {})


def test_subscriber_receives_only_its_topic(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path), write_log=False)
    seen = []
    bus.subscribe(BusTopic.REACTION, lambda m: seen.append(m.payload), "s")
    bus.publish(BusTopic.STIMULUS, "src", {"a": 1})
    bus.publish(BusTopic.REACTION, "src", {"valence": 1.0})
    assert seen == [{"valence": 1.0}]


def test_bad_subscriber_never_breaks_bus(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path), write_log=False)

    def boom(_m):
        raise RuntimeError("bad subscriber")

    bus.subscribe(BusTopic.STIMULUS, boom, "bad")
    bus.publish(BusTopic.STIMULUS, "src", {})  # must not raise
    assert bus.message_count() == 1


def test_replay_matches_published(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path))
    for i in range(5):
        bus.publish(BusTopic.TELEMETRY, "src", {"i": i}, step=i)
    replayed = bus.replay_jsonl(bus.log_path)
    assert len(replayed) == 5
    assert [m.payload["i"] for m in replayed] == list(range(5))


def test_snapshot_shape(tmp_path):
    bus = ConscienceBus(state_dir=str(tmp_path))
    bus.publish(BusTopic.OPS_EVENT, "src", {})
    snap = bus.snapshot()
    assert snap["published_total"] == 1
    assert "trace" in snap and snap["log_path"]
