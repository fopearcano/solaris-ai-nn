"""Alpha CLI: help, init, doctor, modules, run-demo, cycle-status, strict."""

from __future__ import annotations

import os
import subprocess
import sys

from solaris_ai_nn.cli import main

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _module_help() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "solaris_ai_nn", "--help"],
        capture_output=True, text=True, timeout=60, cwd=_ROOT)


def test_module_help_works():
    result = _module_help()
    assert result.returncode == 0
    assert "Alpha Research System" in result.stdout


def test_init_command(tmp_path):
    rc = main(["init", "--state-dir", str(tmp_path / "a")])
    assert rc == 0
    assert os.path.isfile(str(tmp_path / "a" / "ALPHA_STATE_MANIFEST.json"))


def test_doctor_command(tmp_path):
    rc = main(["doctor", "--state-dir", str(tmp_path / "a")])
    assert rc == 0


def test_modules_command(tmp_path):
    rc = main(["modules", "--state-dir", str(tmp_path / "a")])
    assert rc == 0


def test_run_demo_command(tmp_path):
    rc = main(["run-demo", "--state-dir", str(tmp_path / "a"), "--max-ticks",
               "25"])
    assert rc == 0
    assert os.path.isfile(
        str(tmp_path / "a" / "reports" / "ALPHA_RESEARCH_SYSTEM_REPORT.md"))


def test_cycle_status_command(tmp_path):
    rc = main(["cycle-status", "--state-dir", str(tmp_path / "a")])
    assert rc == 0


def test_artifact_index_and_runbook_and_report(tmp_path):
    sd = str(tmp_path / "a")
    assert main(["run-demo", "--state-dir", sd, "--max-ticks", "25"]) == 0
    assert main(["artifact-index", "--state-dir", sd]) == 0
    assert main(["build-runbook", "--state-dir", sd]) == 0
    assert main(["build-report", "--state-dir", sd]) == 0


def test_alpha_group(tmp_path):
    assert main(["alpha", "doctor", "--state-dir", str(tmp_path / "a")]) == 0


def test_strict_mode_handles_blockers(tmp_path):
    # require_claimguard + strict turns a missing ClaimGuard into nonzero exit;
    # if ClaimGuard is present the command still returns an int exit code.
    rc = main(["doctor", "--state-dir", str(tmp_path / "a"), "--strict",
               "--require-claimguard"])
    assert rc in (0, 2)
