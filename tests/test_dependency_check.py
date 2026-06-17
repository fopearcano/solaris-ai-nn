"""Dependency check: required pass, optional warning, missing required blocker."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import (
    DependencyCheck,
    DependencyCheckResult,
    DependencyFinding,
    DependencyKind,
)


def test_required_dependency_pass():
    result = DependencyCheck().check()
    # numpy + solaris_ai_nn are required and importable in the test env.
    names = {f.name: f for f in result.findings}
    assert names["numpy"].available is True
    assert names["solaris_ai_nn"].available is True
    assert result.passed is True


def test_optional_dependency_warning():
    r = DependencyCheckResult(python_ok=True)
    r.findings.append(DependencyFinding(
        "psutil", DependencyKind.EXTERNAL_FEEDER_OPTIONAL, available=False))
    assert r.passed is True
    assert len(r.warnings) == 1


def test_missing_required_dependency_blocker():
    r = DependencyCheckResult(python_ok=True)
    r.findings.append(DependencyFinding(
        "numpy", DependencyKind.REQUIRED, available=False))
    assert r.passed is False
    assert r.blockers


def test_no_install_attempted():
    d = DependencyCheck().check().to_dict()
    assert d["installs_anything"] is False
    # Every finding carries an install hint instead of installing.
    for f in d["findings"]:
        assert "install_hint" in f
