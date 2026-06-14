"""Pilot4ReadinessDossierBuilder: MD+JSON; planning-only conclusion; scanned."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot4_planning import (
    ConsentBoundary,
    ForbiddenActuatorRegistry,
    Pilot4PlanningConfig,
    Pilot4ReadinessConclusion,
    Pilot4ReadinessDossierBuilder,
    RiskModel,
    ThreatModel,
)


def _build(tmp_path, pilot3=None):
    cfg = Pilot4PlanningConfig(base_dir=str(tmp_path))
    return Pilot4ReadinessDossierBuilder(base_dir=str(tmp_path)).build(
        config=cfg, forbidden=ForbiddenActuatorRegistry(),
        risk=RiskModel().default_assessment("network_action"),
        consent=ConsentBoundary(), threat=ThreatModel(), pilot3=pilot3)


def test_markdown_and_json_generated(tmp_path):
    cfg = Pilot4PlanningConfig(base_dir=str(tmp_path))
    builder = Pilot4ReadinessDossierBuilder(base_dir=str(tmp_path))
    dossier = builder.build_and_write(config=cfg)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "PILOT4_READINESS_DOSSIER.md"))
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "PILOT4_READINESS_DOSSIER.json"))
    assert "dossier_paths" in dossier.sections


def test_conclusion_planning_only_not_ready(tmp_path):
    dossier = _build(tmp_path)
    assert dossier.conclusion in Pilot4ReadinessConclusion.ALL
    assert dossier.conclusion in (
        Pilot4ReadinessConclusion.NOT_READY_FOR_REAL_ACTUATION,
        Pilot4ReadinessConclusion.REQUIRES_ARCHITECTURE_REVISION)


def test_critical_firewall_finding_requires_revision(tmp_path):
    dossier = _build(tmp_path, pilot3={
        "firewall_audit": {"critical_finding_count": 1}})
    assert dossier.conclusion == \
        Pilot4ReadinessConclusion.REQUIRES_ARCHITECTURE_REVISION


def test_missing_pilot3_data_reported(tmp_path):
    dossier = _build(tmp_path, pilot3=None)
    assert dossier.sections["pilot3_data_present"] is False
    assert any("not available" in str(dossier.sections[
        "pilot3_firewall_summary"]) for _ in [0]) or \
        any("not available" in b for b in dossier.sections["blockers"])


def test_claim_guard_scans_report(tmp_path):
    dossier = _build(tmp_path)
    assert dossier.claim_guard_safe is True


def test_actuation_prohibited_is_a_blocker(tmp_path):
    dossier = _build(tmp_path)
    assert any("prohibited" in b for b in dossier.sections["blockers"])
