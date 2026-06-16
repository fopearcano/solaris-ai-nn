"""Cycle archive: local metadata; archived cycles stay visible; no deletion."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import ArchiveReason, ResearchCycleArchive


def test_archive_records_visible_and_not_deleted():
    arch = ResearchCycleArchive()
    rec = arch.archive("cycle_1", ArchiveReason.COMPLETED,
                       final_stage="cycle_complete")
    d = rec.to_dict()
    assert d["artifacts_deleted"] is False
    assert d["visible"] is True
    assert d["reason"] == ArchiveReason.COMPLETED


def test_unknown_reason_normalized():
    rec = ResearchCycleArchive().archive("cycle_1", "not_a_reason")
    assert rec.reason == ArchiveReason.UNKNOWN


def test_to_dict_counts():
    arch = ResearchCycleArchive()
    arch.archive("cycle_1", ArchiveReason.COMPLETED)
    arch.archive("cycle_2", ArchiveReason.OPERATOR_ABANDONED)
    d = arch.to_dict()
    assert d["archived_cycle_count"] == 2
    assert "future evidence" in d["note"]
