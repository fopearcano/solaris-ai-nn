"""Console runtime: bounded, console generated, status generated, no control."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_console import TesterConsoleRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def test_bounded_runtime(tmp_path):
    rt = TesterConsoleRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"),
        console_dir=str(tmp_path / "console"), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_console_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True, html=True)
    assert os.path.isfile(os.path.join(rt.console_dir, "INDEX.md"))
    assert os.path.isfile(os.path.join(rt.console_dir, "CONSOLE_REPORT.md"))


def test_status_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    st = rt.console_status()
    assert st["console_available"] is True
    assert "overall_health" in st


def test_no_external_control(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    st = rt.console_status()
    assert st["read_only"] is True
    assert st["runs_server"] is False
    assert st["opens_browser"] is False


def test_does_not_modify_run_artifacts(tmp_path):
    # The console writes only under console_dir; run artifacts are untouched.
    tester = str(tmp_path / "tester")
    rt = build_console(tmp_path, fixture=True)
    # The fixture reports dir still exists and was not deleted.
    assert os.path.isdir(os.path.join(tester, "reports"))


def test_doctor(tmp_path):
    rt = TesterConsoleRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"),
        console_dir=str(tmp_path / "console"))
    doc = rt.run_doctor()
    assert doc["read_only"] is True
    assert doc["runs_server"] is False
