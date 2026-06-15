"""MaturationDetector: marker detected; weak separate; no consciousness language."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import (
    MaturationDetector,
    MaturationMarkerType,
)


def test_marker_detected():
    det = MaturationDetector()
    det.detect({"perceptual_ontogenesis": {"stable_concept_count": 2},
                "semiogenesis": {"stable_sign_count": 1}}, tick=0)
    types = {m.marker_type for m in det.markers}
    assert MaturationMarkerType.FIRST_STABLE_CONCEPT in types
    assert MaturationMarkerType.FIRST_STABLE_SIGN in types


def test_weak_marker_separate():
    det = MaturationDetector()
    # Low prediction success -> a weak "first useful prediction" marker.
    det.detect({"sensorium_cognition": {"prediction_success_rate": 0.1}},
               tick=0)
    assert any(m.marker_type == MaturationMarkerType.FIRST_USEFUL_PREDICTION
               for m in det.weak_markers)
    assert all(m.marker_type != MaturationMarkerType.FIRST_USEFUL_PREDICTION
               for m in det.markers)


def test_no_consciousness_milestone_language():
    det = MaturationDetector()
    det.detect({"perceptual_ontogenesis": {"stable_concept_count": 1}}, tick=0)
    note = det.markers[0].to_dict()["note"].lower()
    assert "not a consciousness" in note


def test_first_occurrence_only():
    det = MaturationDetector()
    det.detect({"perceptual_ontogenesis": {"stable_concept_count": 2}}, tick=0)
    det.detect({"perceptual_ontogenesis": {"stable_concept_count": 5}}, tick=1)
    # The "first stable concept" marker is recorded only once.
    firsts = [m for m in det.markers
              if m.marker_type == MaturationMarkerType.FIRST_STABLE_CONCEPT]
    assert len(firsts) == 1
