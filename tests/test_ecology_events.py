"""Tests for ecology event primitives."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ecology.events import (
    ECOLOGY_NOTE,
    EcologyEvent,
    EcologyEventType,
    EcologyStimulus,
    StimulusSource,
)


def test_seventeen_event_types():
    assert len(EcologyEventType.ALL) == 17


def test_three_sources():
    assert len(StimulusSource.ALL) == 3
    assert StimulusSource.DEVELOPMENTAL_NURSERY in StimulusSource.ALL


def test_absence_like_subset():
    assert EcologyEventType.ABSENCE_WINDOW in EcologyEventType.ABSENCE_LIKE
    assert EcologyEventType.QUIET_PHASE in EcologyEventType.ABSENCE_LIKE
    assert EcologyEventType.SCARCITY_EVENT in EcologyEventType.ABSENCE_LIKE
    assert EcologyEventType.REGULAR_SIGNAL not in \
        EcologyEventType.ABSENCE_LIKE


def test_stimulus_clamps_intensity_and_auto_id():
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           intensity=5.0, step=3)
    assert stim.intensity == 1.0
    assert stim.stimulus_id == "eco_3_regular_signal"
    low = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                          intensity=-2.0)
    assert low.intensity == 0.0


def test_is_absence_property():
    absence = EcologyStimulus(event_type=EcologyEventType.ABSENCE_WINDOW)
    signal = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL)
    assert absence.is_absence is True
    assert signal.is_absence is False


def test_unknown_event_type_rejected():
    with pytest.raises(ValueError):
        EcologyStimulus(event_type="not_a_real_event")


def test_to_dict_carries_provenance_note():
    stim = EcologyStimulus(event_type=EcologyEventType.NOVEL_SIGNAL)
    data = stim.to_dict()
    assert data["note"] == ECOLOGY_NOTE
    assert data["is_absence"] is False


def test_event_wraps_stimulus():
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           step=4)
    event = EcologyEvent(stimulus=stim, regime="mixed_nursery",
                         cycle_phase="day", season="spring", step=4)
    data = event.to_dict()
    assert data["regime"] == "mixed_nursery"
    assert data["stimulus"]["event_type"] == "regular_signal"
