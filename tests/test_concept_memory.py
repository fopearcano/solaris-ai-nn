"""ConceptMemoryStore: append-only; decayed not deleted; rejected preserved."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptMemoryStore,
    ProtoConcept,
    ProtoConceptKind,
    ProtoConceptStatus,
)


def test_append_only_records(tmp_path):
    store = ConceptMemoryStore(state_dir=str(tmp_path))
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3})
    store.record_concept(c.to_dict())
    store.record_atom({"atom_id": "ATOM_1"})
    store.write_index()
    assert os.path.isfile(tmp_path / "concepts.jsonl")
    assert os.path.isfile(tmp_path / "atoms.jsonl")
    assert os.path.isfile(tmp_path / "concept_index.json")


def test_decayed_concept_not_deleted(tmp_path):
    store = ConceptMemoryStore(state_dir=str(tmp_path))
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3})
    store.record_concept(c.to_dict())
    # Decay is recorded as new state, not deletion.
    store.record_concept_state(c.concept_id, ProtoConceptStatus.DECAYING,
                               {"reasons": ["not_seen_again"]})
    history = store.concept_history(c.concept_id)
    assert len(history) == 2  # original + state change both retained
    assert store.index.concepts[c.concept_id]["status"] == \
        ProtoConceptStatus.DECAYING


def test_rejected_concept_preserved(tmp_path):
    store = ConceptMemoryStore(state_dir=str(tmp_path))
    c = ProtoConcept(kind=ProtoConceptKind.UNKNOWN,
                     modality_distribution={"radio_frequency": 1})
    store.record_concept(c.to_dict())
    store.record_concept_state(c.concept_id, ProtoConceptStatus.REJECTED,
                               {"reasons": ["false_pattern"]})
    # Rejected concept remains in the index and the append-only log.
    assert c.concept_id in store.index.concepts
    lines = open(tmp_path / "concepts.jsonl").read().strip().splitlines()
    assert len(lines) == 2


def test_relations_recorded(tmp_path):
    store = ConceptMemoryStore(state_dir=str(tmp_path))
    store.record_relation({"relation_id": "REL_1", "relation_type": "precedes"})
    assert os.path.isfile(tmp_path / "relations.jsonl")
    assert "REL_1" in store.index.relations
