"""SensoriumProfile: human-like/non-human/mixed valid; labels not ground truth."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import SensoriumProfileBuilder, SensoriumProfileType


def test_human_like_profile_valid():
    p = SensoriumProfileBuilder().build(
        SensoriumProfileType.HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE)
    assert "human_textual" in p.enabled_modalities
    assert p.human_labels_as_ground_truth is False


def test_non_human_profile_valid():
    p = SensoriumProfileBuilder().build(
        SensoriumProfileType.RF_ECHO_VIBRATION_MAGNETIC)
    assert "radio_frequency" in p.enabled_modalities
    assert "human_textual" not in p.enabled_modalities


def test_mixed_profile_valid():
    p = SensoriumProfileBuilder().build(
        SensoriumProfileType.MIXED_HUMAN_NONHUMAN)
    assert "human_textual" in p.enabled_modalities
    assert "radio_frequency" in p.enabled_modalities


def test_human_labels_never_ground_truth():
    for ptype in SensoriumProfileType.ALL:
        p = SensoriumProfileBuilder().build(ptype)
        assert p.human_labels_as_ground_truth is False
        assert p.to_dict()["human_labels_as_ground_truth"] is False


def test_passive_profile_disables_structure():
    p = SensoriumProfileBuilder().build(SensoriumProfileType.PASSIVE_EVENT_LIST)
    assert p.passive_only is True
    assert p.receptor_adaptation_enabled is False
