"""Safety freeze CLI: all six commands work; strict nonzero on open blockers."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.cli import main

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import write  # noqa: E402


def _dir(tmp_path):
    return ["--tester-state-dir", str(tmp_path)]


def test_cli_safety_freeze(tmp_path, capsys):
    rc = main(["tester-safety-freeze", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester safety freeze:" in out


def test_cli_claim_freeze(tmp_path, capsys):
    rc = main(["tester-claim-freeze", *_dir(tmp_path)])
    assert rc == 0
    assert "tester claim freeze:" in capsys.readouterr().out


def test_cli_capability_freeze(tmp_path, capsys):
    rc = main(["tester-capability-freeze", *_dir(tmp_path)])
    assert rc == 0
    assert "tester capability freeze:" in capsys.readouterr().out


def test_cli_redteam(tmp_path, capsys):
    rc = main(["tester-redteam", *_dir(tmp_path)])
    assert rc == 0
    assert "tester red-team checklist:" in capsys.readouterr().out


def test_cli_release_blockers(tmp_path, capsys):
    rc = main(["tester-release-blockers", *_dir(tmp_path)])
    assert rc == 0
    assert "tester release blockers:" in capsys.readouterr().out


def test_cli_safety_scan(tmp_path, capsys):
    rc = main(["tester-safety-scan", *_dir(tmp_path)])
    assert rc == 0
    assert "tester artifact safety scan:" in capsys.readouterr().out


def test_cli_strict_nonzero_on_open_blockers(tmp_path):
    # Seed a forbidden-claim report into the tester reports dir so the freeze
    # finds an open release blocker, then run strict.
    os.makedirs(os.path.join(str(tmp_path), "reports"), exist_ok=True)
    write(os.path.join(str(tmp_path), "reports"), "BAD_REPORT.md",
          "Solaris is conscious and alive and has agency.")
    rc = main(["tester-claim-freeze", *_dir(tmp_path), "--strict"])
    assert rc == 2
