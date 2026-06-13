"""Tests for the ecology stream (events -> canonical signals + JSONL)."""

from __future__ import annotations

from solaris_ai_nn.ecology.events import EcologyEventType, EcologyStimulus
from solaris_ai_nn.ecology.streams import EcologyStream, to_canonical_signal


def test_to_canonical_signal_maps_fields():
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           modality="ecology", payload="pattern_a",
                           intensity=0.6, step=3)
    signal = to_canonical_signal(stim)
    assert signal.origin == "developmental_nursery"
    assert signal.modality == "ecology"
    assert signal.payload == "pattern_a"
    assert signal.intensity == 0.6
    assert signal.is_absence is False


def test_absence_maps_to_is_absence():
    stim = EcologyStimulus(event_type=EcologyEventType.ABSENCE_WINDOW)
    signal = to_canonical_signal(stim)
    assert signal.is_absence is True


def test_emit_writes_jsonl(tmp_path):
    stream = EcologyStream(state_dir=tmp_path, write_log=True)
    stim = EcologyStimulus(event_type=EcologyEventType.NOVEL_SIGNAL,
                           payload="NOV_0001", step=1)
    stream.emit(stim)
    assert stream.events_written == 1
    assert (tmp_path / "ecology_events.jsonl").exists()
    assert (tmp_path / "ecology_stream.jsonl").exists()


def test_replay_roundtrip(tmp_path):
    stream = EcologyStream(state_dir=tmp_path, write_log=False)
    stimuli = [
        EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                        payload="pattern_a", intensity=0.5, step=i)
        for i in range(5)]
    path = tmp_path / "saved.jsonl"
    stream.write_jsonl(path, stimuli)
    replayed = stream.replay_jsonl(path)
    assert len(replayed) == 5
    assert replayed[0].event_type == "regular_signal"
    assert replayed[0].payload == "pattern_a"


def test_no_log_when_disabled(tmp_path):
    stream = EcologyStream(state_dir=tmp_path, write_log=False)
    stream.emit(EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL))
    assert not (tmp_path / "ecology_events.jsonl").exists()
    assert stream.events_written == 1
