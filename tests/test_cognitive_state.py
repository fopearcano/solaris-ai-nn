"""SensoriumCognitiveState: serializes; no subjective language; debug-only summary."""

from __future__ import annotations

from solaris_ai_nn.sensorium_cognition import (
    CognitiveFocus,
    CognitivePressure,
    SensoriumCognitiveState,
)


def test_state_serializes():
    state = SensoriumCognitiveState(
        focus=CognitiveFocus(active_signs=["SIGN_1"]),
        pressure=CognitivePressure(question_pressure=0.4))
    d = state.to_dict()
    assert d["focus"]["active_signs"] == ["SIGN_1"]
    assert d["pressure"]["question_pressure"] == 0.4


def test_no_subjective_mind_state_language():
    state = SensoriumCognitiveState()
    note = state.to_dict()["note"].lower()
    assert "not a subjective mind-state" in note
    assert "not human-language thought" in note
    assert "operational pressures, not feelings" in \
        state.pressure.to_dict()["note"].lower()


def test_human_readable_summary_debug_only():
    state = SensoriumCognitiveState(
        focus=CognitiveFocus(active_signs=["a", "b"]))
    summary = state.debug_summary()
    assert summary.startswith("[debug-gloss]")
    assert state.to_dict()["debug_summary"] == summary
