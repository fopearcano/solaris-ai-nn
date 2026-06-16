"""Membrane activation: normalized, gloss not truth, pulse not command, fallback."""

from __future__ import annotations

from solaris_ai_nn.live_birth import (
    EnvironmentalMembraneActivation,
    LiveEventEnvelope,
    LiveSensoryEvent,
)


def _accepted(source_id="chronos_absence", is_absence=False, gloss="x"):
    raw = {"event_id": f"ev_{source_id}", "timestamp_utc": "t",
           "source_id": source_id, "modality": "m", "channel": "c",
           "read_only": True, "is_command": False,
           "human_label_is_ground_truth": False, "payload": {"v": 1},
           "quality": {"completeness": 1.0, "noise": 0.0,
                       "is_absence": is_absence, "is_noisy": False},
           "debug_gloss": gloss}
    env = LiveEventEnvelope(raw=raw, source_file="f", line_number=1)
    env.event = LiveSensoryEvent.from_dict(raw)
    return env


def test_accepted_events_normalized():
    result = EnvironmentalMembraneActivation().activate(
        [_accepted(), _accepted("operator_pulse")])
    assert result.activated is True
    assert result.normalized_count == 2


def test_debug_gloss_not_ground_truth():
    act = EnvironmentalMembraneActivation()
    act.activate([_accepted(gloss="DEBUG ONLY")])
    for ev in act.last_batch.events:
        assert ev["debug_gloss_is_ground_truth"] is False
        assert ev["human_label_is_ground_truth"] is False


def test_operator_pulse_not_command():
    act = EnvironmentalMembraneActivation()
    act.activate([_accepted("operator_pulse")])
    for ev in act.last_batch.events:
        if ev["source_id"] == "operator_pulse":
            assert ev["is_command"] is False
            assert ev["stimulus"] is True


def test_first_event_markers():
    result = EnvironmentalMembraneActivation().activate([
        _accepted("chronos_absence", is_absence=True),
        _accepted("operator_pulse")])
    assert result.first_event_id
    assert result.first_absence_event_id
    assert result.first_operator_pulse_id


def test_read_only_and_no_control():
    d = EnvironmentalMembraneActivation().activate([_accepted()]).to_dict()
    assert d["read_only"] is True
    assert d["controls_feeders"] is False
    assert d["requests_more_data"] is False
    assert d["treats_text_as_command"] is False
