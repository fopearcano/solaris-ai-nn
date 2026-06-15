"""SensoryField: persists across ticks; pressures update; not an event list."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import Receptor, SensoryField
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def _receptor(power):
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    r.observe(SensoryEventEnvelope(source_id="rf", source_kind="fixture_replay",
                                   modality="radio_frequency",
                                   features={"power": power}))
    return r


def test_field_persists_across_ticks():
    field = SensoryField()
    r = _receptor(0.5)
    field.update([r], novelty=0.6)
    tick1 = field.tick
    field.update([r], novelty=0.1)
    assert field.tick == tick1 + 1
    assert field.continuity.tick_count == 2


def test_pressure_values_update():
    field = SensoryField()
    r = _receptor(0.8)
    state = field.update([r], novelty=0.9, absence=0.3)
    assert state.novelty_pressure > 0.0
    assert state.absence_pressure > 0.0
    assert 0.0 <= state.stability <= 1.0


def test_pressure_decays_and_carries():
    field = SensoryField()
    r = _receptor(0.5)
    field.update([r], novelty=0.9)
    high = field.pressures["novelty"].value
    field.update([r], novelty=0.0)
    # The pressure carried over (continuous), decaying rather than resetting.
    assert 0.0 < field.pressures["novelty"].value < high


def test_not_just_event_list():
    field = SensoryField()
    # The field exposes pressures / dominant modality / stability -- a state,
    # not a list of raw events.
    r = _receptor(0.5)
    field.update([r])
    d = field.to_dict()
    assert "pressures" in d and "stability" in d
    assert "events" not in d
