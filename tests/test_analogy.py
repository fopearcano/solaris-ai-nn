"""AnalogyEngine: structural analogy; bad analogy recorded; no semantics."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import AnalogyEngine


def test_structural_analogy_created():
    # Same kind (rhythm) across different modalities -> structural analogy.
    rf = InternalSign(kind=SignKind.RHYTHM, sign_code="rhy:01",
                      modality_distribution={"radio_frequency": 4})
    vib = InternalSign(kind=SignKind.RHYTHM, sign_code="rhy:02",
                       modality_distribution={"vibration": 4})
    analogies = AnalogyEngine().detect([rf, vib])
    assert analogies
    assert analogies[0].structural_basis


def test_bad_analogy_recorded_if_contradicted():
    rf = InternalSign(kind=SignKind.RHYTHM,
                      modality_distribution={"radio_frequency": 4})
    vib = InternalSign(kind=SignKind.RHYTHM,
                       modality_distribution={"vibration": 4})
    engine = AnalogyEngine()
    analogies = engine.detect([rf, vib])
    analogies[0].mark_contradicted()
    # Contradicted analogy is kept (recorded), not deleted.
    assert analogies[0].contradicted is True
    assert engine.contradicted_count == 1


def test_no_human_semantic_requirement():
    rf = InternalSign(kind=SignKind.RHYTHM,
                      modality_distribution={"radio_frequency": 4})
    vib = InternalSign(kind=SignKind.RHYTHM,
                       modality_distribution={"vibration": 4})
    a = AnalogyEngine().detect([rf, vib])[0]
    assert "structural analogy, not semantic" in a.to_dict()["note"]


def test_same_modality_no_analogy():
    a = InternalSign(kind=SignKind.RHYTHM,
                     modality_distribution={"radio_frequency": 4})
    b = InternalSign(kind=SignKind.RHYTHM,
                     modality_distribution={"radio_frequency": 4})
    # Same kind AND same modality -> not a cross-modality analogy.
    assert AnalogyEngine().detect([a, b]) == []
