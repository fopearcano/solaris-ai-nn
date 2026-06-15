"""SensoriumPerspective: frame updates; shift recorded; no subjective viewpoint."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import PerspectiveFrame, SensoriumPerspective


def test_perspective_frame_updates():
    p = SensoriumPerspective()
    p.update(PerspectiveFrame(active_modality="radio_frequency",
                              dominant_receptor="radio_frequency"))
    assert p.frame.active_modality == "radio_frequency"


def test_perspective_shift_recorded():
    p = SensoriumPerspective()
    p.update(PerspectiveFrame(active_modality="radio_frequency",
                              dominant_receptor="radio_frequency"))
    shift = p.update(PerspectiveFrame(active_modality="vibration",
                                      dominant_receptor="vibration"),
                     reason="dominant changed")
    assert shift is not None
    assert len(p.shifts) == 1
    assert shift.from_signature != shift.to_signature


def test_no_shift_on_same_frame():
    p = SensoriumPerspective()
    frame = PerspectiveFrame(active_modality="rf", dominant_receptor="rf",
                             attention_focus="x")
    p.update(frame)
    shift = p.update(PerspectiveFrame(active_modality="rf",
                                      dominant_receptor="rf",
                                      attention_focus="x"))
    assert shift is None


def test_no_subjective_point_of_view_language():
    p = SensoriumPerspective()
    p.update(PerspectiveFrame(active_modality="rf"))
    note = p.frame.to_dict()["note"].lower()
    assert "not a subjective point-of-view" in note
