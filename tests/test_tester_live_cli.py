"""Tester live CLI: all six commands work; strict returns nonzero on blocker."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.cli import main

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_live_helpers import approve_governance  # noqa: E402


def _dirs(tmp_path):
    return ["--state-dir", str(tmp_path / "live"),
            "--tester-state-dir", str(tmp_path / "tester")]


def test_cli_tester_live_init(tmp_path, capsys):
    rc = main(["tester-live-init", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live-read-only init:" in out


def test_cli_tester_live_doctor(tmp_path, capsys):
    main(["tester-live-init", *_dirs(tmp_path)])
    rc = main(["tester-live-doctor", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live doctor:" in out


def test_cli_tester_live_samples(tmp_path, capsys):
    rc = main(["tester-live-samples", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live sample event packs:" in out


def test_cli_tester_live_run(tmp_path, capsys):
    main(["tester-live-init", *_dirs(tmp_path)])
    approve_governance(str(tmp_path / "live"))
    rc = main(["tester-live-run", *_dirs(tmp_path), "--no-write-templates",
               "--copy-safe-samples", "--run-birth", "--run-membrane",
               "--run-integration", "--run-observation"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live-read-only run:" in out


def test_cli_tester_live_bundle(tmp_path, capsys):
    main(["tester-live-init", *_dirs(tmp_path)])
    rc = main(["tester-live-bundle", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live bundle:" in out
    assert "local only: True" in out


def test_cli_tester_live_checklist(tmp_path, capsys):
    rc = main(["tester-live-checklist",
               "--tester-state-dir", str(tmp_path / "tester")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester live checklist:" in out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    # Disabled governance + strict doctor -> nonzero.
    main(["tester-live-init", *_dirs(tmp_path)])
    rc = main(["tester-live-doctor", *_dirs(tmp_path), "--strict"])
    assert rc == 2
