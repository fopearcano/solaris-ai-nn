"""Live recurrence tracker: recurrence detected; single/operator insufficient."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    LiveFeatureExtractor,
    LiveRecurrenceTracker,
    RecurrenceStrength,
)


def _ev(eid, sid, payload, channel="c"):
    return {"event_id": eid, "timestamp_utc": "2026-06-18T08:00:00Z",
            "source_id": sid, "modality": "scalar", "channel": channel,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False},
            "debug_gloss": "", "debug_gloss_is_ground_truth": False}


def _vectors(events):
    return LiveFeatureExtractor().extract(accepted_events=events).vectors


def test_recurrence_detected():
    events = [_ev(f"e{i}", "machine_body", {"load": 0.3}) for i in range(5)]
    patterns = LiveRecurrenceTracker(min_recurrence=3).track(_vectors(events))
    assert len(patterns) == 1
    assert patterns[0].count == 5
    assert patterns[0].strength in (RecurrenceStrength.MODERATE,
                                    RecurrenceStrength.STRONG)


def test_single_event_insufficient():
    patterns = LiveRecurrenceTracker(min_recurrence=3).track(
        _vectors([_ev("e1", "machine_body", {"load": 0.3})]))
    assert patterns[0].strength == RecurrenceStrength.NONE


def test_operator_text_recurrence_insufficient():
    events = [_ev(f"o{i}", "operator_pulse", {"pulse": 1}) for i in range(5)]
    patterns = LiveRecurrenceTracker(min_recurrence=3).track(_vectors(events))
    assert patterns[0].operator_only is True
    assert patterns[0].contamination_risk  # recorded, never hidden
