"""Packaging runtime: bounded, reports + guide + manifest, no install/network."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_packaging import TesterPackagingRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_packaging_helpers import run_packaging  # noqa: E402


def test_bounded_runtime(tmp_path):
    rt = TesterPackagingRuntime(tester_state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = run_packaging(tmp_path)
    reports = os.path.join(rt.packaging_dir, "reports")
    assert os.path.isfile(os.path.join(reports, "PACKAGING_REPORT.md"))
    assert os.path.isfile(os.path.join(reports, "PACKAGING_REPORT.json"))


def test_install_guide_generated(tmp_path):
    rt = run_packaging(tmp_path)
    assert os.path.isfile(os.path.join(
        rt.packaging_dir, "install_guides", "TESTER_INSTALL_GUIDE.md"))


def test_manifest_generated(tmp_path):
    rt = run_packaging(tmp_path)
    assert os.path.isfile(os.path.join(
        rt.packaging_dir, "manifests", "TESTER_RELEASE_ARTIFACT_MANIFEST.json"))


def test_no_install_network_git_shell_publish(tmp_path):
    rt = run_packaging(tmp_path)
    snap = rt.safety.snapshot()
    assert snap["can_install_packages"] is False
    assert snap["can_access_network"] is False
    assert snap["can_run_git"] is False
    assert snap["can_run_shell"] is False
    assert snap["can_publish"] is False
    st = rt.packaging_status()
    assert st["installs_packages"] is False
    assert st["publishes"] is False


def test_doctor_method(tmp_path):
    rt = TesterPackagingRuntime(tester_state_dir=str(tmp_path))
    doc = rt.run_doctor()
    assert "doctor_health" in doc
