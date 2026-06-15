"""ProtoConcept: serializes; neutral operational name; label not ground truth."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ProtoConcept,
    ProtoConceptKind,
    neutral_operational_name,
)


def test_proto_concept_serializes():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4},
                     recurrence_count=4)
    d = c.to_dict()
    assert d["kind"] == ProtoConceptKind.MODALITY_NATIVE
    assert "not a word" in d["note"]
    assert d["limitations"]


def test_neutral_operational_name_not_human_label():
    name = neutral_operational_name("radio_frequency",
                                    ProtoConceptKind.MODALITY_NATIVE)
    assert name.startswith("rf_pattern_")
    # No human semantic label like person/object/room/dog.
    for human in ("person", "object", "room", "dog", "sentence"):
        assert human not in name


def test_concept_auto_generates_neutral_name():
    c = ProtoConcept(kind=ProtoConceptKind.RHYTHM_BASED,
                     modality_distribution={"vibration": 3})
    assert c.operational_name
    assert c.operational_name.startswith("vib_pattern_")


def test_human_label_is_external_annotation_only():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"human_textual": 2})
    c.attach_human_annotation("dog")
    assert c.human_annotations == ["dog"]
    # Annotation raises contamination but is not treated as ground truth.
    assert c.human_label_contamination_score > 0.0
    assert "dog" not in c.operational_name


def test_cross_modal_and_absence_flags():
    cross = ProtoConcept(kind=ProtoConceptKind.CROSS_MODAL,
                         modality_distribution={"radio_frequency": 1,
                                                "vibration": 1})
    absent = ProtoConcept(kind=ProtoConceptKind.ABSENCE_BASED,
                          modality_distribution={"radio_frequency": 1})
    assert cross.is_cross_modal is True
    assert absent.is_absence_based is True
