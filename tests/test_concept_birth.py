"""ConceptBirthEngine: repeated invariant -> candidate; isolated -> weak/none."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptBirthEngine,
    ConceptBirthTrigger,
    PerceptualAtom,
    PerceptualAtomKind,
)


def test_repeated_invariant_creates_candidate():
    atom = PerceptualAtom(kind=PerceptualAtomKind.INVARIANT,
                          modality="radio_frequency", source_id="rf_feed",
                          recurrence_count=5, novelty=0.6,
                          provenance_refs=["invariant:INV_1"])
    cands = ConceptBirthEngine().propose([atom])
    assert len(cands) == 1
    assert cands[0].weak is False
    assert cands[0].trigger == ConceptBirthTrigger.REPEATED_INVARIANT
    assert cands[0].evidence_refs  # evidence preserved


def test_isolated_event_creates_weak_or_none():
    # An isolated low-novelty flux atom should not create even a weak concept.
    isolated = PerceptualAtom(kind=PerceptualAtomKind.FLUX,
                              modality="radio_frequency", recurrence_count=1,
                              novelty=0.1)
    assert ConceptBirthEngine().propose([isolated]) == []
    # An isolated but high-novelty atom may create a weak/unstable candidate.
    novel = PerceptualAtom(kind=PerceptualAtomKind.ABSENCE,
                           modality="radio_frequency", recurrence_count=1,
                           novelty=0.8)
    cands = ConceptBirthEngine().propose([novel])
    assert len(cands) == 1 and cands[0].weak is True


def test_fixture_only_concept_marked():
    atom = PerceptualAtom(kind=PerceptualAtomKind.INVARIANT,
                          modality="radio_frequency", recurrence_count=4,
                          origin="fixture")
    cand = ConceptBirthEngine().propose([atom])[0]
    assert cand.concept.fixture_grounded is True
    assert cand.concept.live_grounded is False


def test_human_annotation_atom_marks_contamination():
    atom = PerceptualAtom(kind=PerceptualAtomKind.HUMAN_ANNOTATION,
                          modality="human_textual", source_id="text_feed")
    cand = ConceptBirthEngine().propose([atom])[0]
    assert cand.concept.human_label_contamination_score == 1.0
    assert any("label" in lim for lim in cand.concept.limitations)
