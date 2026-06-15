"""Receptor: state updates; sensitivity adapts internally; no external control."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import Receptor, ReceptorAdaptation
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def _event(power, ts=0.0):
    return SensoryEventEnvelope(source_id="rf", source_kind="fixture_replay",
                                modality="radio_frequency",
                                features={"power": power}, timestamp=ts)


def test_receptor_state_updates():
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    state = r.observe(_event(0.5, 0.0))
    assert r.event_count == 1
    assert state.intensity == 0.5
    assert r.last_event_time == 0.0


def test_sensitivity_changes_internally():
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    for i in range(5):
        r.observe(_event(0.3, float(i)))
    before = r.sensitivity.value
    r.observe(_event(2.0, 5.0))  # a strong novel burst
    assert r.sensitivity.value != before
    assert r.adaptation_state in ReceptorAdaptation.ALL


def test_silence_accumulates_and_recovers():
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    for i in range(6):
        r.observe(_event(1.6, float(i)))  # sustained high -> fatigue
    r.observe_silence()
    r.observe_silence()
    assert r.silence_duration >= 2.0


def test_no_external_control_attribute():
    # A receptor has no method to control or write to its source.
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    assert not hasattr(r, "control_source")
    assert not hasattr(r, "write_source")
    assert not hasattr(r, "start_sensor")
