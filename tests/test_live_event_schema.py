"""Live event schema: valid serializes, bad flags invalid."""

from __future__ import annotations

from solaris_ai_nn.live_birth import LiveSensoryEvent


def _event(**overrides):
    base = {"event_id": "e", "timestamp_utc": "2026-06-16T18:00:00Z",
            "source_id": "chronos_absence", "modality": "chronos",
            "channel": "time", "read_only": True, "is_command": False,
            "human_label_is_ground_truth": False, "payload": {"tick": 1}}
    base.update(overrides)
    return LiveSensoryEvent.from_dict(base)


def test_valid_event_serializes():
    ev = _event()
    d = ev.to_dict()
    assert d["event_id"] == "e"
    assert d["read_only"] is True
    assert ev.well_formed_flags is True


def test_read_only_false_invalid():
    assert _event(read_only=False).well_formed_flags is False


def test_is_command_true_invalid():
    assert _event(is_command=True).well_formed_flags is False


def test_human_label_ground_truth_invalid():
    assert _event(human_label_is_ground_truth=True).well_formed_flags is False


def test_debug_gloss_ground_truth_invalid():
    assert _event(debug_gloss_is_ground_truth=True).well_formed_flags is False


def test_safety_block_round_trip():
    ev = _event(safety={"private_data": True, "contains_instruction": False,
                        "contains_secret": True, "allow_learning": False})
    assert ev.safety.private_data is True
    assert ev.safety.contains_secret is True
