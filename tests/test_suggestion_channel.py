"""Tests for NeuralSuggestion + SuggestionChannel."""

from __future__ import annotations

import json

from solaris_ai_nn.experiments.solaris_sidecar_observation import FakeBus
from solaris_ai_nn.integration.suggestion_channel import (
    ACTION_SUGGESTION,
    DESIRE_SUGGESTION,
    NeuralSuggestion,
    SuggestionChannel,
)


def _suggestion(confidence=0.7, **kw) -> NeuralSuggestion:
    return NeuralSuggestion(
        suggested_type=kw.pop("suggested_type", ACTION_SUGGESTION),
        payload={"action": "approach"}, confidence=confidence,
        substrate_type="esn", reason="test", **kw)


def test_stores_suggestions_marked_uncommitted():
    channel = SuggestionChannel(publish_enabled=False)
    channel.submit(_suggestion())
    assert len(channel.suggestions) == 1
    stored = channel.suggestions[0]
    assert stored.committed is False
    assert stored.to_dict()["committed"] is False
    assert stored.kind == "NeuralSuggestion"


def test_committed_suggestion_is_rejected_as_unsafe():
    channel = SuggestionChannel()
    bad = _suggestion()
    bad.committed = True  # someone tries to smuggle a committed action
    published = channel.submit(bad)
    assert published is False
    assert len(channel.suggestions) == 0
    assert len(channel.rejected) == 1
    assert "no action authority" in channel.rejected[0]["rejection_reason"]


def test_unknown_type_rejected():
    channel = SuggestionChannel()
    assert channel.submit(_suggestion(suggested_type="CommandSuggestion")) is False
    assert channel.rejected[0]["rejection_reason"].startswith("unknown suggestion type")


def test_publishes_to_bus_when_enabled():
    bus = FakeBus()
    channel = SuggestionChannel(bus=bus, publish_enabled=True)
    assert channel.submit(_suggestion()) is True
    assert channel.published_count == 1
    assert isinstance(bus.published[0], NeuralSuggestion)


def test_publish_disabled_stores_only():
    bus = FakeBus()
    channel = SuggestionChannel(bus=bus, publish_enabled=False)
    assert channel.submit(_suggestion()) is False
    assert bus.published == []
    assert len(channel.suggestions) == 1


def test_confidence_distribution():
    channel = SuggestionChannel(publish_enabled=False)
    for c in (0.1, 0.3, 0.5, 0.9, 0.95):
        channel.submit(_suggestion(confidence=c))
    dist = channel.confidence_distribution()
    assert dist["count"] == 5
    assert dist["min"] == 0.1 and dist["max"] == 0.95
    assert abs(dist["mean"] - 0.55) < 1e-9
    assert sum(dist["buckets"].values()) == 5
    assert dist["buckets"]["0.8-1.0"] == 2


def test_last_and_jsonl_export(tmp_path):
    channel = SuggestionChannel(publish_enabled=False)
    channel.submit(_suggestion(suggested_type=DESIRE_SUGGESTION))
    channel.submit(_suggestion())
    assert len(channel.last(1)) == 1
    path = tmp_path / "suggestions.jsonl"
    assert channel.to_jsonl(path) == 2
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert all(row["committed"] is False for row in rows)


def test_snapshot():
    channel = SuggestionChannel(publish_enabled=False)
    channel.submit(_suggestion())
    snap = channel.snapshot()
    assert snap["stored"] == 1
    assert snap["published"] == 0
    assert "confidence" in snap
