"""Evidence continuity ledger: append-only, preservation, supersede, persist."""

from __future__ import annotations

import os

from solaris_ai_nn.research_cycle import (
    EvidenceContinuityLedger,
    EvidenceContinuityStatus,
    EvidenceLedgerEntryType,
)


def test_negative_falsified_missing_preserved(tmp_path):
    ledger = EvidenceContinuityLedger(state_dir=str(tmp_path), persist=False)
    for kind in (EvidenceLedgerEntryType.NEGATIVE,
                 EvidenceLedgerEntryType.FALSIFICATION,
                 EvidenceLedgerEntryType.MISSING):
        entry = ledger.add(kind, summary="x")
        assert entry.status == EvidenceContinuityStatus.PRESERVED
    idx = ledger.index()
    assert idx["negative_evidence_entry_count"] == 1
    assert idx["falsified_evidence_entry_count"] == 1
    assert idx["missing_evidence_entry_count"] == 1
    assert idx["append_only"] is True


def test_supersede_marks_not_deletes(tmp_path):
    ledger = EvidenceContinuityLedger(state_dir=str(tmp_path), persist=False)
    ledger.add(EvidenceLedgerEntryType.BASELINE, summary="v1")
    count = ledger.supersede(EvidenceLedgerEntryType.BASELINE)
    assert count == 1
    # entry is still present, just superseded.
    assert len(ledger.entries) == 1
    assert ledger.entries[0].status == EvidenceContinuityStatus.SUPERSEDED


def test_persist_writes_jsonl_and_index(tmp_path):
    ledger = EvidenceContinuityLedger(state_dir=str(tmp_path))
    ledger.add(EvidenceLedgerEntryType.BASELINE, summary="v1")
    assert os.path.isfile(os.path.join(str(tmp_path), "evidence_ledger.jsonl"))
    assert os.path.isfile(os.path.join(str(tmp_path), "evidence_index.json"))


def test_unknown_type_falls_back_inconclusive(tmp_path):
    ledger = EvidenceContinuityLedger(state_dir=str(tmp_path), persist=False)
    entry = ledger.add("not_a_real_type", summary="x")
    assert entry.entry_type == EvidenceLedgerEntryType.INCONCLUSIVE
