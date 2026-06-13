"""Tests for the evidence ledger."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.evidence import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
)


def test_nine_evidence_types():
    assert len(EvidenceType.ALL) == 9


def test_evidence_writes_jsonl(tmp_path):
    ledger = EvidenceLedger(state_dir=tmp_path)
    ledger.record(EvidenceRecord(
        hypothesis_id="h1", evidence_type=EvidenceType.NURSERY_SIMULATED,
        source_scope="nursery_simulation", observation="ok"))
    assert (tmp_path / "hypothesis_evidence.jsonl").exists()
    assert ledger.snapshot()["evidence_count"] == 1


def test_offline_evidence_marked_offline(tmp_path):
    ledger = EvidenceLedger(state_dir=tmp_path)
    rec = ledger.record(EvidenceRecord(
        hypothesis_id="h1", evidence_type=EvidenceType.LATENT_REPLAY,
        source_scope="latent_replay", observation="replayed"))
    assert rec.is_offline is True
    assert any("offline" in lim.lower() for lim in rec.limitations)


def test_source_scope_preserved(tmp_path):
    ledger = EvidenceLedger(state_dir=tmp_path)
    rec = ledger.record(EvidenceRecord(
        hypothesis_id="h1", evidence_type=EvidenceType.SUPPORTING,
        source_scope="nursery_simulation", observation="ok"))
    assert rec.source_scope == "nursery_simulation"


def test_for_hypothesis_filters(tmp_path):
    ledger = EvidenceLedger(state_dir=tmp_path)
    ledger.record(EvidenceRecord(hypothesis_id="h1",
                                 evidence_type=EvidenceType.SUPPORTING))
    ledger.record(EvidenceRecord(hypothesis_id="h2",
                                 evidence_type=EvidenceType.WEAKENING))
    assert len(ledger.for_hypothesis("h1")) == 1


def test_internal_trace_is_offline(tmp_path):
    rec = EvidenceRecord(hypothesis_id="h", evidence_type=EvidenceType.SUPPORTING,
                         source_scope="internal_trace_analysis")
    assert rec.is_offline is True
