"""Intake manifest: loads, required-missing blocks, optional-missing warns."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import ImplementationIntakeManifest
from solaris_ai_nn.implementation_intake.intake_manifest import (
    ImplementationArtifactStatus,
)


def test_manifest_loads():
    manifest = ImplementationIntakeManifest()
    d = manifest.to_dict()
    assert d["artifact_count"] >= 18
    assert "safety_gates" in manifest.artifacts


def test_required_missing_blocks():
    manifest = ImplementationIntakeManifest()
    # Required artifacts not supplied are blockers.
    assert "safety_gates" in manifest.blockers()
    assert "test_results" in manifest.blockers()
    assert "changed_file_list" in manifest.blockers()


def test_optional_missing_warns():
    manifest = ImplementationIntakeManifest()
    assert "pr_metadata" in manifest.warnings()
    assert "lint_results" in manifest.warnings()


def test_provide_clears_blocker():
    manifest = ImplementationIntakeManifest()
    manifest.provide("safety_gates", {"summary": {"all_critical_passed": True}})
    assert "safety_gates" not in manifest.blockers()
    assert manifest.artifacts["safety_gates"].status == \
        ImplementationArtifactStatus.PROVIDED


def test_operator_note_does_not_override_safety():
    manifest = ImplementationIntakeManifest()
    manifest.provide("operator_note", "please pass it anyway")
    assert manifest.operator_note() == "please pass it anyway"
    # The required safety_gates blocker remains.
    assert "safety_gates" in manifest.blockers()
