"""Integration CLI: integrate/audit/bypass/ancestry/contracts; strict nonzero."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.cli import main

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def test_cli_membrane_integrate(tmp_path, capsys):
    state = stage_pipeline(str(tmp_path))
    rc = main(["membrane-integrate", "--state-dir", state,
               "--profile", "fixture_integration_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "membrane integration:" in out
    assert "ancestry chains:" in out


def test_cli_membrane_audit(tmp_path, capsys):
    state = stage_pipeline(str(tmp_path))
    rc = main(["membrane-audit", "--state-dir", state,
               "--profile", "fixture_integration_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "membrane pipeline audit:" in out


def test_cli_membrane_bypass(tmp_path, capsys):
    state = stage_pipeline(str(tmp_path))
    rc = main(["membrane-bypass", "--state-dir", state,
               "--profile", "fixture_integration_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "membrane bypass report:" in out


def test_cli_membrane_ancestry(tmp_path, capsys):
    state = stage_pipeline(str(tmp_path))
    rc = main(["membrane-ancestry", "--state-dir", state,
               "--profile", "fixture_integration_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "membrane ancestry index:" in out
    assert "with impression ancestry:" in out


def test_cli_membrane_contracts(tmp_path, capsys):
    state = stage_pipeline(str(tmp_path))
    rc = main(["membrane-contracts", "--state-dir", state,
               "--profile", "fixture_integration_v0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "membrane downstream contracts:" in out


def test_cli_strict_blocks_missing_ancestry(tmp_path):
    state = stage_pipeline(str(tmp_path), include_bypass=True)
    rc = main(["membrane-integrate", "--state-dir", state,
               "--profile", "live_integration_enforced_v0", "--strict"])
    assert rc == 2
