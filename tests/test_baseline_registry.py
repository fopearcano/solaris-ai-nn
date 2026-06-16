"""Baseline registry: record created, append-only history, blocked visible."""

from __future__ import annotations

import os

from solaris_ai_nn.post_merge_assimilation import (
    BaselineRecord,
    BaselineRegistry,
    BaselineStatus,
)


def test_baseline_record_created(tmp_path):
    reg = BaselineRegistry(state_dir=str(tmp_path))
    reg.register(BaselineRecord(baseline_id="b0",
                                status=BaselineStatus.VALIDATED))
    assert reg.get("b0") is not None
    assert reg.status()["baseline_record_count"] == 1
    assert os.path.isfile(tmp_path / "baseline_registry.json")
    assert os.path.isfile(tmp_path / "baseline_evidence_index.json")


def test_append_only_history(tmp_path):
    reg = BaselineRegistry(state_dir=str(tmp_path))
    reg.register(BaselineRecord(baseline_id="b1",
                                status=BaselineStatus.CANDIDATE))
    reg.update_status("b1", BaselineStatus.VALIDATED_WITH_WARNINGS,
                      reason="one warning")
    reg.update_status("b1", BaselineStatus.REGRESSION_WATCH, reason="drifted")
    rec = reg.get("b1")
    # History grows; the record is not overwritten/deleted.
    assert len(rec.status_history) >= 3
    assert rec.status == BaselineStatus.REGRESSION_WATCH


def test_blocked_baseline_visible(tmp_path):
    reg = BaselineRegistry(state_dir=str(tmp_path))
    reg.register(BaselineRecord(baseline_id="b2",
                                status=BaselineStatus.BLOCKED_BY_SAFETY))
    assert reg.get("b2").blocked is True
    assert reg.status()["blocked_baseline_count"] == 1


def test_load_round_trips(tmp_path):
    reg = BaselineRegistry(state_dir=str(tmp_path))
    reg.register(BaselineRecord(baseline_id="b0",
                                status=BaselineStatus.VALIDATED))
    reg2 = BaselineRegistry(state_dir=str(tmp_path))
    reg2.load()
    assert "b0" in reg2.records


def test_no_deletion_in_source():
    import inspect

    from solaris_ai_nn.post_merge_assimilation import baseline_registry

    src = inspect.getsource(baseline_registry)
    assert "del self.records" not in src
    assert ".pop(" not in src or "payload.pop" in src  # only loader pops keys
