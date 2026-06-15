"""PerceptualAtom: serializes; provenance; human annotation marked external."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    PerceptualAtom,
    PerceptualAtomKind,
    PerceptualAtomSource,
    PerceptualAtomTrace,
)


def test_atom_serializes():
    atom = PerceptualAtom(kind=PerceptualAtomKind.INVARIANT,
                          modality="radio_frequency", source_id="rf_feed",
                          recurrence_count=3,
                          provenance_refs=["invariant:INV_1"])
    d = atom.to_dict()
    assert d["kind"] == PerceptualAtomKind.INVARIANT
    assert d["modality"] == "radio_frequency"
    assert d["recurrence_count"] == 3
    assert "not a concept" in d["note"]


def test_provenance_and_signature_present():
    atom = PerceptualAtom(kind=PerceptualAtomKind.RHYTHM, modality="vibration",
                          source_id="vib_feed",
                          provenance_refs=["rhythm:vib_feed"])
    assert atom.provenance_refs == ["rhythm:vib_feed"]
    assert atom.signature  # stable structural key always present


def test_human_annotation_marked_external():
    atom = PerceptualAtom(kind=PerceptualAtomKind.HUMAN_ANNOTATION,
                          modality="human_textual", source_id="text_feed")
    assert atom.human_annotation_external is True
    assert atom.origin == PerceptualAtomSource.HUMAN_ANNOTATION
    assert "human_label_external" in atom.contamination_flags


def test_observe_again_increments_recurrence():
    atom = PerceptualAtom(kind=PerceptualAtomKind.FLUX, modality="thermal")
    assert atom.is_recurrent is False
    atom.observe_again(timestamp=5.0)
    assert atom.recurrence_count == 2
    assert atom.is_recurrent is True


def test_atom_trace_records_observations():
    trace = PerceptualAtomTrace(atom_id="ATOM_1")
    trace.record({"recurrence_count": 1})
    trace.record({"recurrence_count": 2})
    assert trace.to_dict()["observation_count"] == 2
