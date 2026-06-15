"""SyntaxPatternBuilder: sequence + absence patterns; no human grammar forced."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignKind,
    SyntaxPatternBuilder,
    SyntaxRelation,
)


def _signs():
    rf = InternalSign(kind=SignKind.MODALITY_NATIVE,
                      modality_distribution={"radio_frequency": 4},
                      source_distribution={"feed": 4}, proto_concept_refs=["C1"])
    vib = InternalSign(kind=SignKind.MODALITY_NATIVE,
                       modality_distribution={"vibration": 4},
                       source_distribution={"feed": 4},
                       proto_concept_refs=["C2"])
    absence = InternalSign(kind=SignKind.ABSENCE,
                           modality_distribution={"radio_frequency": 1},
                           proto_concept_refs=["C3"])
    return rf, vib, absence


def test_sequence_pattern_detected():
    rf, vib, absence = _signs()
    relations = [{"source_concept": "C1", "target_concept": "C2",
                  "relation_type": "predicts", "strength": 0.7}]
    patterns = SyntaxPatternBuilder().build([rf, vib, absence],
                                            concept_relations=relations)
    rels = {p.relation for p in patterns}
    assert SyntaxRelation.PREDICTS in rels


def test_absence_pattern_detected():
    rf, vib, absence = _signs()
    patterns = SyntaxPatternBuilder().build([rf, vib, absence])
    rels = {p.relation for p in patterns}
    assert SyntaxRelation.AFTER_ABSENCE in rels


def test_no_human_grammar_forced():
    rf, vib, absence = _signs()
    patterns = SyntaxPatternBuilder().build([rf, vib, absence])
    assert patterns
    for p in patterns:
        assert "not human grammar" in p.to_dict()["note"]
        # No subject/verb/object roles are present.
        assert "subject" not in p.to_dict()
        assert "verb" not in p.to_dict()


def test_density_bounded():
    rf, vib, absence = _signs()
    builder = SyntaxPatternBuilder()
    builder.build([rf, vib, absence])
    assert 0.0 <= builder.density(3) <= 1.0
