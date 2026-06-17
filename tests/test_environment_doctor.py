"""Environment doctor: result generated, blockers, warnings, no side effects."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_packaging import (
    EnvironmentDoctorResult,
    EnvironmentFinding,
    EnvironmentHealth,
    TesterEnvironmentDoctor,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_doctor_result_generated(tmp_path):
    result = TesterEnvironmentDoctor(
        tester_state_dir=str(tmp_path)).check()
    assert result.findings
    assert result.overall_health in EnvironmentHealth.ALL


def test_missing_required_module_blocks():
    r = EnvironmentDoctorResult()
    r.findings.append(EnvironmentFinding(
        "package_import", EnvironmentHealth.BLOCKED, required=True))
    assert r.passed is False
    assert r.blockers


def test_missing_optional_module_warns():
    r = EnvironmentDoctorResult()
    r.findings.append(EnvironmentFinding(
        "live_tester_templates_present", EnvironmentHealth.MISSING,
        required=False))
    assert r.passed is True
    assert r.warnings


def test_no_network_shell_install(tmp_path):
    d = TesterEnvironmentDoctor(tester_state_dir=str(tmp_path)).check().to_dict()
    assert d["auto_fixes"] is False
    assert d["runs_demos"] is False
    assert d["installs"] is False
    assert d["accesses_network"] is False
