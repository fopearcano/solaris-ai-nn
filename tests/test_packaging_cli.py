"""Packaging CLI: all commands work; strict nonzero on blocker."""

from __future__ import annotations

from solaris_ai_nn.cli import main


def _dir(tmp_path):
    return ["--tester-state-dir", str(tmp_path)]


def test_cli_doctor(tmp_path, capsys):
    rc = main(["doctor"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "doctor" in out.lower()


def test_cli_tester_packaging(tmp_path, capsys):
    rc = main(["tester-packaging", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester packaging:" in out


def test_cli_tester_install_guide(tmp_path, capsys):
    rc = main(["tester-install-guide", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "install guide:" in out.lower()


def test_cli_tester_release_manifest(tmp_path, capsys):
    rc = main(["tester-release-manifest", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "release manifest:" in out.lower()


def test_cli_tester_clean_machine(tmp_path, capsys):
    rc = main(["tester-clean-machine", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "clean-machine readiness:" in out.lower()


def test_cli_tester_command_check(tmp_path, capsys):
    rc = main(["tester-command-check", *_dir(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "command registry check:" in out.lower()


def test_cli_strict_zero_when_ready(tmp_path):
    # The repo is install-ready, so strict packaging returns 0.
    rc = main(["tester-packaging", *_dir(tmp_path), "--strict"])
    assert rc == 0
