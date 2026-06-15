"""GlossBuilder: approximate gloss; not ground truth; contaminated marked."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    GlossBuilder,
    GlossStatus,
    InternalSign,
    SignGrounding,
    SignKind,
)


def test_approximate_gloss_generated():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4},
                     grounding_score=0.7)
    gloss = GlossBuilder().build(s)
    # A modality-native sign is always glossed approximately, never as a word.
    assert gloss.status == GlossStatus.APPROXIMATE
    assert gloss.text.startswith("~")


def test_gloss_not_ground_truth():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4})
    gloss = GlossBuilder().build(s)
    assert "not ground truth" in gloss.to_dict()["note"]


def test_contaminated_gloss_marked():
    s = InternalSign(kind=SignKind.HUMAN_LABEL_CONTAMINATED,
                     grounding=SignGrounding.LABEL_GROUNDED,
                     modality_distribution={"human_textual": 4})
    gloss = GlossBuilder().build(s)
    assert gloss.status == GlossStatus.HUMAN_LABEL_CONTAMINATED


def test_no_overtranslation_into_human_object_category():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4})
    gloss = GlossBuilder().build(s)
    # The gloss describes structure, never a concrete human object category.
    for human in ("dog", "person", "room", "car", "house"):
        assert human not in gloss.text.lower()


def test_gloss_dependence_score():
    clean = InternalSign(kind=SignKind.MODALITY_NATIVE,
                         modality_distribution={"radio_frequency": 4})
    contaminated = InternalSign(kind=SignKind.HUMAN_LABEL_CONTAMINATED,
                                modality_distribution={"human_textual": 4})
    builder = GlossBuilder()
    builder.build(clean)
    builder.build(contaminated)
    score = GlossBuilder.dependence_score([clean, contaminated])
    assert 0.0 <= score <= 1.0
    assert score == 0.5
