"""CrossModalDetector: relations detected; no human object ontology required."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import CrossModalDetector
from solaris_ai_nn.plural_sensorium.cross_modal import CrossModalRelationType


def test_cross_modal_relation_detected():
    det = CrossModalDetector(coincidence_window=0.5, sequence_window=5.0)
    det.observe("radio_frequency", "rf", 0.0, 0.9)
    rels = det.observe("vibration", "vib", 0.3, 0.7)
    assert rels
    rel = rels[0]
    assert rel.modality_a == "radio_frequency"
    assert rel.modality_b == "vibration"
    assert rel.relation_type in (CrossModalRelationType.COINCIDES_WITH,
                                 CrossModalRelationType.FOLLOWED_BY)


def test_repeated_relation_accumulates_support():
    det = CrossModalDetector()
    for t in range(4):
        det.observe("radio_frequency", "rf", float(t * 2), 0.9)
        det.observe("vibration", "vib", float(t * 2) + 0.3, 0.7)
    rel = det.all_relations()[0]
    assert rel.support >= 2


def test_no_human_object_ontology():
    # The relation is described purely in modality terms, never as objects
    # ("person", "chair", "room", etc).
    det = CrossModalDetector()
    det.observe("radio_frequency", "rf", 0.0, 0.9)
    det.observe("ultrasound_echo", "echo", 0.2, 0.5)
    rel = det.all_relations()[0]
    blob = str(rel.to_dict()).lower()
    for human_label in ("person", "dog", "chair", "room", "object", "sentence"):
        assert human_label not in blob


def test_shared_silence_relation():
    det = CrossModalDetector()
    rel = det.record_shared_silence(["radio_frequency", "vibration"])
    assert rel is not None
    assert rel.relation_type == CrossModalRelationType.SHARED_SILENCE
