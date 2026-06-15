"""SignContaminationAnalyzer: word-as-code; gloss replacing sign; dominance."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    GlossStatus,
    InternalSign,
    SignContaminationAnalyzer,
    SignGrounding,
    SignKind,
)


def test_human_word_as_sign_code_detected():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="dog",
                     modality_distribution={"radio_frequency": 3})
    rep = SignContaminationAnalyzer().analyze(s)
    assert "human_word_used_as_sign_code" in rep.flags
    assert rep.feature_grounded is False


def test_gloss_replacing_sign_detected():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3},
                     grounding_score=0.0)
    s.attach_gloss("a dog barking", GlossStatus.HUMAN_LABEL_CONTAMINATED)
    rep = SignContaminationAnalyzer().analyze(s)
    assert "gloss_replacing_sign" in rep.flags or \
        "contaminated_gloss_attached" in rep.flags


def test_text_stream_dominance_detected():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"human_textual": 8,
                                            "radio_frequency": 1})
    rep = SignContaminationAnalyzer().analyze(s)
    assert "text_stream_dominates_sign_formation" in rep.flags
    assert rep.contamination_score >= 0.5


def test_label_grounded_flagged():
    s = InternalSign(kind=SignKind.HUMAN_LABEL_CONTAMINATED,
                     grounding=SignGrounding.LABEL_GROUNDED,
                     modality_distribution={"human_textual": 4})
    rep = SignContaminationAnalyzer().analyze(s)
    assert rep.contamination_score >= 0.5
    assert "never ground truth" in rep.to_dict()["note"]


def test_clean_sign_feature_grounded():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:03a",
                     modality_distribution={"radio_frequency": 6},
                     grounding_score=0.8)
    rep = SignContaminationAnalyzer().analyze(s)
    assert rep.feature_grounded is True


def test_contaminated_ratio():
    clean = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                         modality_distribution={"radio_frequency": 6},
                         grounding_score=0.8)
    dirty = InternalSign(kind=SignKind.HUMAN_LABEL_CONTAMINATED,
                         modality_distribution={"human_textual": 6})
    analyzer = SignContaminationAnalyzer()
    reports = analyzer.analyze_all([clean, dirty])
    assert analyzer.contaminated_ratio(reports) == 0.5
