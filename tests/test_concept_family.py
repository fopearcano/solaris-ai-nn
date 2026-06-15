"""ConceptFamilyBuilder: families built; multi-membership; no human taxonomy."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptFamilyBuilder,
    ConceptFamilyType,
    ProtoConcept,
    ProtoConceptKind,
)


def test_families_built():
    concepts = [
        ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3}),
        ProtoConcept(kind=ProtoConceptKind.ABSENCE_BASED,
                     modality_distribution={"radio_frequency": 1}),
    ]
    families = ConceptFamilyBuilder().build(concepts)
    types = {f.family_type for f in families}
    assert ConceptFamilyType.RF in types
    assert ConceptFamilyType.ABSENCE in types


def test_concept_can_belong_to_multiple_families():
    # A cross-modal RF+vibration concept joins RF, vibration, and cross-modal.
    c = ProtoConcept(kind=ProtoConceptKind.CROSS_MODAL,
                     modality_distribution={"radio_frequency": 2,
                                            "vibration": 2})
    builder = ConceptFamilyBuilder()
    builder.build([c])
    member_of = [ft for ft, fam in builder.families.items()
                 if c.concept_id in fam.members]
    assert ConceptFamilyType.CROSS_MODAL in member_of
    assert ConceptFamilyType.RF in member_of
    assert ConceptFamilyType.VIBRATION in member_of
    assert len(member_of) >= 3


def test_no_human_taxonomy_required():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"alien_rf": 2})
    fam = ConceptFamilyBuilder().build([c])[0]
    # Family is a structural cluster, explicitly not a human taxonomy.
    assert "not a human taxonomy" in fam.to_dict()["note"]


def test_dominant_family_and_distribution():
    concepts = [ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                             modality_distribution={"radio_frequency": 3})
                for _ in range(3)]
    builder = ConceptFamilyBuilder()
    builder.build(concepts)
    assert builder.dominant_family() == ConceptFamilyType.RF
    assert builder.distribution()[ConceptFamilyType.RF] == 3
