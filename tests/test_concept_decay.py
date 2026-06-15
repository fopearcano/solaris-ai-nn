"""ConceptDecayEngine: records reason; preserves evidence; merge/split recorded."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptDecayEngine,
    DecayReason,
    ProtoConcept,
    ProtoConceptKind,
    ProtoConceptStatus,
)


def test_decay_records_reason():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4},
                     recurrence_count=4, prediction_utility=0.0,
                     compression_utility=0.0)
    res = ConceptDecayEngine().evaluate(c, seen_this_tick=True)
    assert res.decayed is True
    assert DecayReason.PREDICTION_FAILED in res.reasons
    assert c.status == ProtoConceptStatus.DECAYING


def test_evidence_preserved_on_decay():
    c = ProtoConcept(kind=ProtoConceptKind.UNKNOWN,
                     modality_distribution={"radio_frequency": 1},
                     recurrence_count=1, attention_utility=0.0)
    res = ConceptDecayEngine().evaluate(c, seen_this_tick=True)
    # Decay never deletes; the concept is retained with a note.
    assert "evidence is preserved" in res.to_dict()["note"]
    assert any("historical evidence" in lim for lim in c.limitations)


def test_false_pattern_rejected():
    c = ProtoConcept(kind=ProtoConceptKind.UNKNOWN,
                     modality_distribution={"radio_frequency": 1},
                     recurrence_count=1, stability_score=0.0,
                     attention_utility=0.0)
    res = ConceptDecayEngine().evaluate(c, seen_this_tick=True)
    assert DecayReason.FALSE_PATTERN in res.reasons
    assert c.status == ProtoConceptStatus.REJECTED


def test_merge_recorded():
    weaker = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                          modality_distribution={"radio_frequency": 2})
    stronger = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                            modality_distribution={"radio_frequency": 6})
    res = ConceptDecayEngine().merge(weaker, stronger)
    assert res.reasons == [DecayReason.MERGED]
    assert weaker.status == ProtoConceptStatus.MERGED
    assert stronger.concept_id in weaker.parent_concepts


def test_split_recorded():
    parent = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                          modality_distribution={"radio_frequency": 6})
    children = [ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                             modality_distribution={"radio_frequency": 3})
                for _ in range(2)]
    res = ConceptDecayEngine().split(parent, children)
    assert res.reasons == [DecayReason.SPLIT]
    assert parent.status == ProtoConceptStatus.SPLIT
    assert len(parent.child_concepts) == 2
