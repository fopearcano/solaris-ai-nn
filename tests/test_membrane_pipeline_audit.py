"""Pipeline audit: stages walked, fallback/bypass surfaced, strict blocks."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.membrane_integration import (
    MembraneIntegrationRuntime,
    PipelineAuditStatus,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def _run(tmp_path, *, include_bypass=False, strict=False):
    state = stage_pipeline(str(tmp_path), include_bypass=include_bypass)
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0", strict=strict)
    rt.run()
    return rt


def test_all_pipeline_stages_present(tmp_path):
    rt = _run(tmp_path)
    stages = {s.stage for s in rt.audit.stages}
    assert {"live_birth_event_validation", "membrane_impression_generation",
            "ontogenesis_impression_usage",
            "semiogenesis_ancestry_preservation",
            "cognition_ancestry_preservation",
            "scientific_claims_evidence_typing", "alpha_reporting"} <= stages


def test_clean_pipeline_passes(tmp_path):
    rt = _run(tmp_path)
    assert rt.audit.overall_status in (
        PipelineAuditStatus.PASS, PipelineAuditStatus.PASS_WITH_WARNINGS)


def test_ontogenesis_stage_records_impressions(tmp_path):
    rt = _run(tmp_path)
    onto = next(s for s in rt.audit.stages
                if s.stage == "ontogenesis_impression_usage")
    assert onto.impression_count >= 1
    assert onto.fallback_count == 0


def test_bypass_pipeline_strict_blocks(tmp_path):
    rt = _run(tmp_path, include_bypass=True, strict=True)
    # Missing ancestry produces a bypass; strict mode escalates the audit.
    assert rt.audit.overall_status in (
        PipelineAuditStatus.BLOCKED, PipelineAuditStatus.BYPASS_DETECTED)
