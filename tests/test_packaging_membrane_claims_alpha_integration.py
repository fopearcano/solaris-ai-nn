"""Packaging: membrane commands detected, claim scan, alpha exposes status."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_packaging import (
    CommandRegistryCheck,
    TesterPackagingSafetyValidator,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_packaging_helpers import run_packaging  # noqa: E402


def test_membrane_commands_detected():
    reg = {c.name for c in CommandRegistryCheck().check().commands
           if c.registered}
    for cmd in ("membrane-doctor", "membrane-run", "membrane-integrate",
                "membrane-audit"):
        assert cmd in reg, cmd


def test_claim_safety_scan_blocks_forbidden_claims():
    v = TesterPackagingSafetyValidator()
    assert v.validate_claim_text(
        "the package is conscious and alive").safe is False


def test_alpha_exposes_packaging_status(tmp_path):
    run_packaging(tmp_path)
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_packaging_status(
        tester_state_dir=str(tmp_path))
    assert status["packaging_available"] is True
    assert status["installs_packages"] is False
    assert status["publishes"] is False


def test_alpha_absent_without_packaging(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_packaging_status(
        tester_state_dir=str(tmp_path / "none"))
    assert status["packaging_available"] is False
