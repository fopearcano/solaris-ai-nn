"""SignFamilyBuilder: families built; multi-membership; no human taxonomy."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignFamilyBuilder,
    SignFamilyType,
    SignKind,
)


def test_sign_families_built():
    signs = [
        InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3}),
        InternalSign(kind=SignKind.ABSENCE,
                     modality_distribution={"radio_frequency": 1}),
    ]
    families = SignFamilyBuilder().build(signs)
    types = {f.family_type for f in families}
    assert SignFamilyType.RF in types
    assert SignFamilyType.ABSENCE in types


def test_sign_can_belong_to_multiple_families():
    s = InternalSign(kind=SignKind.CROSS_MODAL,
                     modality_distribution={"radio_frequency": 2,
                                            "vibration": 2})
    builder = SignFamilyBuilder()
    builder.build([s])
    member_of = [ft for ft, fam in builder.families.items()
                 if s.sign_id in fam.members]
    assert SignFamilyType.CROSS_MODAL in member_of
    assert SignFamilyType.RF in member_of
    assert SignFamilyType.VIBRATION in member_of
    assert len(member_of) >= 3


def test_no_human_taxonomy_required():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"alien_rf": 2})
    fam = SignFamilyBuilder().build([s])[0]
    assert "not a human semantic taxonomy" in fam.to_dict()["note"]


def test_dominant_family_and_distribution():
    signs = [InternalSign(kind=SignKind.MODALITY_NATIVE,
                          modality_distribution={"radio_frequency": 3})
             for _ in range(3)]
    builder = SignFamilyBuilder()
    builder.build(signs)
    assert builder.dominant_family() == SignFamilyType.RF
    assert builder.distribution()[SignFamilyType.RF] == 3
