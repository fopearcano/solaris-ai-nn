"""Tests for the stream sensors."""

from __future__ import annotations

import json

from solaris_ai_nn.pilot.stream_sensors import (
    JsonlStreamSensor,
    SilenceWindowSensor,
    SyntheticHeartbeatSensor,
    TextStreamSensor,
    build_stream_sensor,
)
from solaris_ai_nn.signals.canonical import Stimulus


def test_jsonl_stream_sensor_emits_stimulus(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(
        json.dumps({"source": "lab", "modality": "audio",
                    "payload": f"sound {i}", "intensity": 0.6})
        for i in range(3)))
    sensor = JsonlStreamSensor(path=path)
    stimulus = sensor(1)
    assert isinstance(stimulus, Stimulus)
    assert stimulus.origin == "lab"
    assert stimulus.modality == "audio"
    assert stimulus.payload == "sound 0"
    assert stimulus.intensity == 0.6
    assert not stimulus.is_absence
    assert [sensor(i) is not None for i in range(2, 6)] == [
        True, True, False, False]  # exhausted after 3
    assert sensor.exhausted
    assert sensor.emitted == 3


def test_text_stream_sensor_emits_stimulus(tmp_path):
    path = tmp_path / "stream.txt"
    path.write_text("hello room\nsomeone walks by\n")
    sensor = TextStreamSensor(path=path, default_intensity=0.3)
    stimulus = sensor(1)
    assert isinstance(stimulus, Stimulus)
    assert stimulus.modality == "text"
    assert stimulus.payload == "hello room"
    assert stimulus.intensity == 0.3


def test_silence_window_sensor_emits_absence(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps({"payload": "only one"}) + "\n")
    sensor = SilenceWindowSensor(source=JsonlStreamSensor(path=path),
                                 window_steps=3, escalation=0.2)
    results = [sensor(i) for i in range(1, 10)]
    assert results[0] is not None and not results[0].is_absence
    assert results[1] is None and results[2] is None  # inside the window
    absences = [r for r in results if r is not None and r.is_absence]
    assert len(absences) >= 3
    assert absences[0].payload == "stream silence"
    assert absences[1].intensity > absences[0].intensity  # escalates
    assert sensor.absences_emitted == len(absences)


def test_silence_resets_on_new_input():
    feed = [Stimulus(payload="a"), None, None, None, Stimulus(payload="b")]

    def source(step):
        return feed[step] if step < len(feed) else None

    sensor = SilenceWindowSensor(source=source, window_steps=3)
    out = [sensor(i) for i in range(8)]
    assert out[0].payload == "a"
    assert out[3] is not None and out[3].is_absence  # window hit
    assert out[4].payload == "b" and not out[4].is_absence  # reset
    assert out[5] is None  # silence counting restarted


def test_synthetic_heartbeat_sensor():
    sensor = SyntheticHeartbeatSensor(interval_steps=5, intensity=0.2)
    out = [sensor(step) for step in range(1, 16)]
    beats = [s for s in out if s is not None]
    assert len(beats) == 3  # steps 5, 10, 15
    assert all(b.modality == "internal" and b.intensity == 0.2 for b in beats)


def test_build_stream_sensor_detects_format(tmp_path):
    jsonl = tmp_path / "x.jsonl"
    jsonl.write_text(json.dumps({"payload": "e"}) + "\n")
    text = tmp_path / "x.txt"
    text.write_text("line\n")
    assert isinstance(build_stream_sensor(jsonl).source, JsonlStreamSensor)
    assert isinstance(build_stream_sensor(text).source, TextStreamSensor)


def test_sensor_feeds_continuous_runner(tmp_path):
    """The sensor chain plugs into ContinuousRunner as a stimulus provider."""
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(
        json.dumps({"source": "lab", "payload": f"e{i}", "intensity": 0.5})
        for i in range(10)))
    sensor = build_stream_sensor(path, silence_window=4)
    runner = ContinuousRunner(state_dir=str(tmp_path / "state"), max_steps=30,
                              stimulus_provider=sensor, seed=3)
    runner.run()
    assert runner.telemetry.steps == 30
    assert sensor.source.emitted == 10  # every stream event reached the brain
    assert sensor.absences_emitted > 0  # and the silence afterwards did too
