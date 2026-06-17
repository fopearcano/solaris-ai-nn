"""Live sign candidate: serializes, preserves evidence, not a sign before gate."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    LiveSignCandidate,
    SignCandidateStatus,
)


def _candidate():
    c = LiveSignCandidate(sign_id="s1", private_token="sig_live_abc123",
                          linked_concept_ids=["c1"],
                          feature_signature_refs=["sig:c1"])
    c.source_distribution = {"machine_body": 5}
    c.add_support("c1", kind="concept", detail="linked concept")
    c.add_counter("e9", reason="divergent payload")
    return c


def test_candidate_serializes():
    d = _candidate().to_dict()
    assert d["sign_id"] == "s1"
    assert d["private_token"] == "sig_live_abc123"
    assert d["linked_concept_ids"] == ["c1"]


def test_evidence_and_counterevidence_preserved():
    d = _candidate().to_dict()
    assert d["supporting_count"] == 1
    assert d["counter_count"] == 1
    assert d["contradicting_events"][0]["reason"] == "divergent payload"


def test_candidate_not_sign_before_gate():
    c = _candidate()
    assert c.status == SignCandidateStatus.EMERGING
    assert c.is_sign is False
    c.status = SignCandidateStatus.BORN
    assert c.is_sign is True


def test_debug_alias_not_ground_truth():
    c = _candidate()
    c.debug_alias = "human readable hint"
    assert c.to_dict()["debug_alias_is_ground_truth"] is False
