"""Soak research protocols exist; architecture evolution consumes dossier/autopsy."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import soak_revision_proposals
from solaris_ai_nn.architecture_evolution.evidence_mapper import EVIDENCE_SOURCES
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_research_protocols_exist():
    for name in ("developmental_soak_protocol", "soak_preflight_protocol",
                 "daily_packet_protocol", "weekly_review_protocol",
                 "restart_drill_protocol", "control_arm_protocol",
                 "evidence_dossier_protocol", "post_run_autopsy_protocol"):
        assert name in PROTOCOLS


def test_evidence_sources_include_soak():
    assert "developmental_soak_report" in EVIDENCE_SOURCES
    assert "evidence_dossier" in EVIDENCE_SOURCES
    assert "post_run_autopsy" in EVIDENCE_SOURCES


def test_architecture_consumes_dossier_autopsy():
    proposals = soak_revision_proposals({
        "autopsy_recommendation": "revise_architecture",
        "structural_growth_status": "fixture_overfit",
        "regression_count": 1, "plateau_count": 1,
        "evidence_claim_count": 3})
    assert proposals
    targets = {p["target"] for p in proposals}
    assert "revise_sensorium" in targets
    assert all(p["advisory_only"] for p in proposals)


def test_growth_recommends_continue_architecture():
    proposals = soak_revision_proposals({
        "autopsy_recommendation": "continue_architecture",
        "structural_growth_status": "real_structural_growth",
        "evidence_claim_count": 5})
    assert any(p["target"] == "continue_architecture" for p in proposals)
