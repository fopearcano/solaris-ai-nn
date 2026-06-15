"""SignBirthEngine: stable concept -> sign; noise -> none; label -> contaminated."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ProtoConcept,
    ProtoConceptKind,
    ProtoConceptStatus,
)
from solaris_ai_nn.semiogenesis import (
    SignBirthEngine,
    SignBirthTrigger,
    SignStatus,
)


def test_stable_concept_creates_sign():
    concept = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        status=ProtoConceptStatus.STABLE,
        modality_distribution={"radio_frequency": 5}, recurrence_count=5,
        stability_score=0.8, prediction_utility=0.7, compression_utility=0.7)
    cands = SignBirthEngine().propose([concept])
    assert len(cands) == 1
    assert cands[0].weak is False
    assert cands[0].sign.status == SignStatus.STABLE
    assert cands[0].trigger == SignBirthTrigger.STABLE_PROTO_CONCEPT


def test_isolated_noise_creates_no_stable_sign():
    noise = ProtoConcept(
        kind=ProtoConceptKind.UNKNOWN, status=ProtoConceptStatus.UNSTABLE,
        modality_distribution={"radio_frequency": 1}, recurrence_count=1,
        stability_score=0.0)
    assert SignBirthEngine().propose([noise]) == []


def test_human_label_born_sign_marked_contaminated():
    concept = ProtoConcept(
        kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
        status=ProtoConceptStatus.EMERGING,
        modality_distribution={"human_textual": 3}, recurrence_count=3,
        human_label_contamination_score=0.9)
    cand = SignBirthEngine().propose([concept])[0]
    assert cand.sign.is_contaminated is True
    assert "concept_human_label_contaminated" in cand.sign.contamination_flags


def test_fixture_grounding_preserved():
    concept = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        status=ProtoConceptStatus.STABLE,
        modality_distribution={"radio_frequency": 4}, recurrence_count=4,
        stability_score=0.7, provenance_refs=["invariant:INV_1"])
    cand = SignBirthEngine().propose([concept])[0]
    assert cand.evidence_refs == ["invariant:INV_1"]
