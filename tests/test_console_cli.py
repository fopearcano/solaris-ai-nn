"""Console CLI: all five commands work; strict nonzero on safety blocker."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.cli import main

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import stage_fixture, stage_forbidden_governance  # noqa: E402


def _dirs(tmp_path):
    return ["--state-dir", str(tmp_path / "live"),
            "--tester-state-dir", str(tmp_path / "tester"),
            "--console-dir", str(tmp_path / "console")]


def test_cli_tester_console(tmp_path, capsys):
    stage_fixture(str(tmp_path / "tester"))
    rc = main(["tester-console", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester console:" in out


def test_cli_tester_console_md(tmp_path, capsys):
    rc = main(["tester-console-md", *_dirs(tmp_path)])
    assert rc == 0
    assert not os.path.isfile(os.path.join(str(tmp_path / "console"),
                                           "INDEX.html"))


def test_cli_tester_console_html(tmp_path, capsys):
    rc = main(["tester-console-html", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "INDEX.html" in out
    assert os.path.isfile(os.path.join(str(tmp_path / "console"), "INDEX.html"))


def test_cli_tester_console_status(tmp_path, capsys):
    rc = main(["tester-console-status", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester console status:" in out


def test_cli_tester_console_runs(tmp_path, capsys):
    stage_fixture(str(tmp_path / "tester"))
    rc = main(["tester-console-runs", *_dirs(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester console runs:" in out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    stage_forbidden_governance(str(tmp_path / "live"))
    rc = main(["tester-console", *_dirs(tmp_path), "--strict"])
    assert rc == 2
