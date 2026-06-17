"""Feedback CLI: all six commands work; strict nonzero on release blocker."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.cli import main

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import sample_path  # noqa: E402


def test_cli_feedback_init(tmp_path, capsys):
    rc = main(["tester-feedback-init", "--tester-state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester feedback init:" in out


def test_cli_feedback_ingest(tmp_path, capsys):
    rc = main(["tester-feedback-ingest", "--tester-state-dir", str(tmp_path),
               "--ingest-path", sample_path("sample_bug_report.json")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester feedback ingest:" in out


def test_cli_feedback_report(tmp_path, capsys):
    main(["tester-feedback-ingest", "--tester-state-dir", str(tmp_path),
          "--ingest-path", sample_path("sample_suggestion.json")])
    rc = main(["tester-feedback-report", "--tester-state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester feedback report:" in out


def test_cli_feedback_ledger(tmp_path, capsys):
    rc = main(["tester-feedback-ledger", "--tester-state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester feedback ledger:" in out


def test_cli_feedback_bundle(tmp_path, capsys):
    rc = main(["tester-feedback-bundle", "--tester-state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester feedback bundle:" in out
    assert "local only: True" in out


def test_cli_feedback_blockers(tmp_path, capsys):
    rc = main(["tester-feedback-blockers", "--tester-state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "release blockers:" in out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    main(["tester-feedback-ingest", "--tester-state-dir", str(tmp_path),
          "--ingest-path", sample_path("sample_release_blocker_feedback.json")])
    rc = main(["tester-feedback-blockers", "--tester-state-dir", str(tmp_path),
               "--strict"])
    assert rc == 2
