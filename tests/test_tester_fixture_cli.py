"""Tester fixture CLI: all six commands work; strict returns nonzero on blocker."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.cli import main


def test_cli_tester_demo(tmp_path, capsys):
    rc = main(["tester-demo", "--state-dir", str(tmp_path),
               "--profile", "fixture_tester_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester fixture demo:" in out
    assert "reproducibility:" in out


def test_cli_tester_golden(tmp_path, capsys):
    rc = main(["tester-golden", "--state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester golden manifest" in out


def test_cli_tester_bundle(tmp_path, capsys):
    rc = main(["tester-bundle", "--state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester artifact bundle:" in out
    assert "local only: True" in out


def test_cli_tester_repro(tmp_path, capsys):
    rc = main(["tester-repro", "--state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester reproducibility check:" in out


def test_cli_tester_regression(tmp_path, capsys):
    rc = main(["tester-regression", "--state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester regression check:" in out


def test_cli_tester_fixtures(tmp_path, capsys):
    rc = main(["tester-fixtures", "--state-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tester fixture pack:" in out
    assert "events:" in out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    # A fixture of only an unsafe command event -> 0 impressions -> strict block.
    fixture = tmp_path / "only_unsafe.jsonl"
    fixture.write_text(json.dumps({
        "event_id": "fx_unsafe_command", "source_id": "operator_pulse",
        "modality": "pulse", "channel": "operator/pulse", "read_only": True,
        "is_command": True, "payload": {"pulse": 1},
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": True,
                   "contains_secret": False, "allow_learning": False},
        "fixture_kind": "unsafe_command"}) + "\n")
    rc = main(["tester-demo", "--state-dir", str(tmp_path / "s"),
               "--fixture-pack-path", str(fixture), "--strict"])
    assert rc == 2
