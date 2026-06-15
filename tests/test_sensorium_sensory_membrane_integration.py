"""Plural sensorium <-> sensory membrane: read-only contract; modality hints."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import family_for_hint
from solaris_ai_nn.plural_sensorium.modality import MODALITY_HINTS, ModalityFamily
from solaris_ai_nn.sensory_membrane.read_only_contract import (
    ReadOnlyContractValidator,
)


def test_read_only_contract_reused():
    # The sensory-membrane read-only contract still rejects write/network/etc.
    v = ReadOnlyContractValidator()
    assert not v.is_read_only_operation("write to source")
    assert not v.is_read_only_operation("network connect")
    assert v.is_read_only_operation("read file")


def test_modality_hints_supported():
    for hint in ("human_textual", "alien_rf", "alien_echo", "alien_thermal",
                 "alien_vibration", "alien_magnetic", "alien_pressure",
                 "alien_field", "machine_rhythm", "absence_silence"):
        fam = family_for_hint(hint)
        assert fam in ModalityFamily.ALL


def test_human_and_alien_hints_distinct():
    assert family_for_hint("human_textual") == ModalityFamily.HUMAN_TEXTUAL
    assert family_for_hint("alien_rf") == ModalityFamily.RADIO_FREQUENCY
    assert "human_textual" in MODALITY_HINTS and "alien_rf" in MODALITY_HINTS
