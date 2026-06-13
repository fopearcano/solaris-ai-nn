"""Tests for state hygiene."""

from __future__ import annotations

from pathlib import Path

from solaris_ai_nn.autoregeneration.state_hygiene import StateHygieneManager


def _setup(tmp_path):
    (tmp_path / "old.jsonl").write_text(
        "".join('{"i":%d}\n' % i for i in range(20)), encoding="utf-8")
    (tmp_path / "corrupt.jsonl").write_text("{bad json\n", encoding="utf-8")
    return StateHygieneManager(state_dir=tmp_path, max_file_bytes=10)


def test_oversized_and_corrupt_detected(tmp_path):
    sh = _setup(tmp_path)
    scan = sh.scan()
    assert "old.jsonl" in scan["oversized"]
    assert "corrupt.jsonl" in scan["corrupt"]


def test_corrupt_quarantined_not_deleted(tmp_path):
    sh = _setup(tmp_path)
    dst = sh.quarantine_file("corrupt.jsonl", reason="bad")
    assert dst is not None
    assert not (tmp_path / "corrupt.jsonl").exists()
    assert (tmp_path / "quarantine").exists()
    assert list((tmp_path / "quarantine").glob("*corrupt.jsonl"))


def test_old_archived_not_deleted(tmp_path):
    sh = _setup(tmp_path)
    dst = sh.archive_file("old.jsonl")
    assert dst is not None
    assert (tmp_path / "archive").exists()


def test_audit_log_written(tmp_path):
    sh = _setup(tmp_path)
    sh.quarantine_file("corrupt.jsonl")
    assert (tmp_path / "repair_audit.jsonl").exists()


def test_source_files_untouched(tmp_path):
    # A path outside the state dir is never moved.
    sh = StateHygieneManager(state_dir=tmp_path)
    outside = tmp_path.parent / "core.py"
    outside.write_text("print('hi')\n", encoding="utf-8")
    assert sh.quarantine_file("../core.py") is None
    assert outside.exists()


def test_evidence_file_recognized(tmp_path):
    sh = StateHygieneManager(state_dir=tmp_path)
    assert sh.is_evidence_file("incidents.jsonl") is True
    assert sh.is_evidence_file("random.jsonl") is False
