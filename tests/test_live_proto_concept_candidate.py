"""Live proto-concept candidate: serializes, preserves evidence, not yet concept."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    LiveProtoConceptCandidate,
    ProtoConceptCandidateStatus,
)


def _candidate():
    c = LiveProtoConceptCandidate(candidate_id="c1", feature_signature="sig")
    c.source_distribution = {"machine_body": 3}
    c.modality_distribution = {"scalar": 3}
    c.recurrence_count = 3
    c.add_support("e1", "machine_body", "")
    c.add_support("e2", "machine_body", "noisy")
    c.add_counter("e3", "machine_body", "divergent payload")
    return c


def test_candidate_serializes():
    d = _candidate().to_dict()
    assert d["candidate_id"] == "c1"
    assert d["recurrence_count"] == 3
    assert d["source_count"] == 1


def test_supporting_and_counter_evidence_preserved():
    c = _candidate()
    d = c.to_dict()
    assert d["supporting_count"] == 2
    assert d["counter_count"] == 1
    assert d["supporting_events"][0]["event_id"] == "e1"
    assert d["contradicting_events"][0]["reason"] == "divergent payload"


def test_candidate_not_concept_before_gate():
    c = _candidate()
    assert c.status == ProtoConceptCandidateStatus.EMERGING
    assert c.is_concept is False
    c.status = ProtoConceptCandidateStatus.BORN
    assert c.is_concept is True


def test_operator_only_flag():
    c = LiveProtoConceptCandidate(candidate_id="c2", feature_signature="s")
    c.source_distribution = {"operator_pulse": 4}
    assert c.operator_only is True
