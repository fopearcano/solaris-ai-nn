"""ConceptContaminationAnalyzer: label-born detected; not ground truth; scored."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptContaminationAnalyzer,
    ProtoConcept,
    ProtoConceptGrounding,
    ProtoConceptKind,
)


def test_label_born_concept_detected():
    c = ProtoConcept(kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
                     grounding=ProtoConceptGrounding.LABEL_GROUNDED,
                     modality_distribution={"human_textual": 4},
                     grounding_score=0.1)
    rep = ConceptContaminationAnalyzer().analyze(c)
    assert rep.feature_grounded is False
    assert "concept_born_primarily_from_human_label" in rep.flags
    assert rep.contamination_score >= 0.5


def test_feature_grounded_concept_clean():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     grounding=ProtoConceptGrounding.FEATURE_GROUNDED,
                     modality_distribution={"radio_frequency": 6},
                     grounding_score=0.8)
    rep = ConceptContaminationAnalyzer().analyze(c)
    assert rep.feature_grounded is True
    assert rep.contamination_score < 0.5


def test_annotation_not_ground_truth():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 2},
                     grounding_score=0.1)
    c.attach_human_annotation("dog")
    rep = ConceptContaminationAnalyzer().analyze(c)
    # An annotation that dominates feature evidence is flagged, never trusted.
    assert "annotation_dominates_feature_evidence" in rep.flags
    assert "never ground truth" in rep.to_dict()["note"]


def test_contamination_score_computed_and_lowers_grounding():
    c = ProtoConcept(kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
                     grounding=ProtoConceptGrounding.LABEL_GROUNDED,
                     modality_distribution={"human_textual": 6},
                     grounding_score=0.6, stability_score=0.6)
    ConceptContaminationAnalyzer().analyze(c)
    # Contamination lowers grounding and stability on the concept.
    assert c.grounding_score < 0.6
    assert c.stability_score < 0.6


def test_contaminated_ratio():
    clean = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                         modality_distribution={"radio_frequency": 6},
                         grounding_score=0.8)
    dirty = ProtoConcept(kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
                         modality_distribution={"human_textual": 6},
                         grounding_score=0.1)
    analyzer = ConceptContaminationAnalyzer()
    reports = analyzer.analyze_all([clean, dirty])
    assert analyzer.contaminated_ratio(reports) == 0.5
