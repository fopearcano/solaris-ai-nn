"""Membrane source pressure: dominance, silence, noise, operator dominance."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import MembraneSourcePressure


def _ev(sid, noisy=False):
    return {"event_id": f"e_{id(object())}", "source_id": sid,
            "modality": "scalar", "channel": "c", "payload": {"v": 1},
            "quality": {"is_absence": False, "is_noisy": noisy},
            "debug_gloss": ""}


def test_source_dominance_detected():
    events = [_ev("machine_body") for _ in range(7)] + [_ev("chronos_absence")]
    a = MembraneSourcePressure().assess(events=events).to_dict()
    assert a["dominant_source"] == "machine_body"
    assert a["membrane_source_pressure_dominance_score"] >= 0.6
    assert a["status"] in ("dominant", "operator_dominated")


def test_silent_source_detected():
    events = [_ev("machine_body") for _ in range(4)]
    a = MembraneSourcePressure().assess(
        events=events, expected_sources=["chronos_absence"]).to_dict()
    assert "chronos_absence" in a["missing_expected_sources"]
    assert a["per_source_status"].get("chronos_absence") == "silent"


def test_noisy_source_present():
    events = [_ev("machine_body", noisy=True) for _ in range(4)]
    a = MembraneSourcePressure().assess(events=events).to_dict()
    assert a["total_events"] == 4


def test_operator_dominance_detected():
    events = [_ev("operator_pulse") for _ in range(6)] + [_ev("machine_body")]
    a = MembraneSourcePressure().assess(events=events).to_dict()
    assert a["status"] == "operator_dominated"
    assert a["membrane_operator_dominance_score"] >= 0.4
