"""Tests for runbook generation."""

from __future__ import annotations

import pytest

from solaris_ai_nn.governance.runbook import (
    RUNBOOK_TYPES,
    RunbookBuilder,
)


def test_bounded_runbook_generated(tmp_path):
    runbook = RunbookBuilder().build("bounded")
    md = runbook.to_markdown()
    for heading in ("Purpose", "Required permissions", "Risk level",
                    "Pre-run checklist", "Launch command",
                    "Monitoring checklist", "Expected artifacts",
                    "Emergency stop procedure", "Post-run review checklist",
                    "Known limitations"):
        assert f"## {heading}" in md, heading
    path = runbook.save(tmp_path / "runbook.md")
    assert path.read_text().startswith("# Runbook: Bounded experiment")


def test_plasticity_runbook_includes_rollback_procedure():
    md = RunbookBuilder().build("plasticity").to_markdown()
    assert "## Rollback procedure (plasticity)" in md
    assert "rollback" in md.lower()
    assert "enable_plasticity_apply" in md  # the approval-gated scope
    assert "plasticity_audit.jsonl" in md


def test_soak_runbooks_include_emergency_stop_procedure():
    for runbook_type in ("soak24", "soak30"):
        md = RunbookBuilder().build(runbook_type).to_markdown()
        assert "## Emergency stop procedure" in md, runbook_type
        assert "EMERGENCY_STOP" in md, runbook_type
        assert "soak_acknowledged=True" in md, runbook_type


def test_all_six_types_build():
    builder = RunbookBuilder()
    assert len(RUNBOOK_TYPES) == 6
    for runbook_type in RUNBOOK_TYPES:
        runbook = builder.build(runbook_type)
        assert runbook.runbook_type == runbook_type
        assert runbook.to_dict()["sections"]


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        RunbookBuilder().build("warp_drive")


def test_runbooks_make_no_consciousness_claims():
    from solaris_ai_nn.governance.compliance import ClaimGuard

    guard = ClaimGuard()
    for runbook_type in RUNBOOK_TYPES:
        md = RunbookBuilder().build(runbook_type).to_markdown()
        assert guard.is_safe(md), runbook_type
