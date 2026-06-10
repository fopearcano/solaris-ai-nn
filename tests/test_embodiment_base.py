"""Tests for embodiment base types (serialization)."""

from __future__ import annotations

from solaris_ai_nn.embodiment.base import ActionResult, EffectorCommand, SensorReading
from solaris_ai_nn.signals import canonical as C


def test_sensor_reading_serializes_and_converts():
    r = SensorReading(sensor="proximity", payload="near:reward", intensity=0.8)
    d = r.to_dict()
    assert d["sensor"] == "proximity" and d["payload"] == "near:reward"
    sig = r.to_signal()
    assert isinstance(sig, C.Stimulus)
    assert sig.payload == "near:reward" and sig.intensity == 0.8
    assert sig.origin == "body:proximity"


def test_absence_reading_flags_signal():
    r = SensorReading(sensor="absence", payload="I sense nothing", is_absence=True)
    assert r.to_signal().is_absence is True


def test_meaning_event_reading():
    r = SensorReading(sensor="object", payload="unknown_object",
                      kind="MeaningEvent", novelty=0.8)
    sig = r.to_signal()
    assert isinstance(sig, C.MeaningEvent)
    assert sig.meaning == "unknown_object" and sig.novelty == 0.8


def test_effector_command_serializes():
    c = EffectorCommand(action="move_north", source="suggestion", params={"x": 1})
    d = c.to_dict()
    assert d == {"action": "move_north", "source": "suggestion", "params": {"x": 1}}


def test_action_result_serializes_and_moved():
    r = ActionResult(action="move_north", executed=True,
                     position_before=(1, 1), position_after=(1, 0),
                     energy_cost=1.0, events=["on:reward_marker"])
    d = r.to_dict()
    assert d["moved"] is True
    assert d["position_after"] == [1, 0]
    blocked = ActionResult(action="move_north", executed=True,
                           position_before=(1, 1), position_after=(1, 1),
                           blocked_reason="wall")
    assert blocked.moved is False
    assert blocked.to_dict()["blocked_reason"] == "wall"
