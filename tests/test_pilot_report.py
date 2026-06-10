"""Tests for the pilot report builder."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.pilot.pilot_manifest import PilotManifest
from solaris_ai_nn.pilot.pilot_report import (
    PilotRecommendation,
    PilotReportBuilder,
    recommend,
)


def _manifest(tmp_path):
    return PilotManifest(profile="simulated", operator="tester",
                         state_dir=str(tmp_path / "state"),
                         artifact_dir=str(tmp_path / "pilots"),
                         max_steps=50, notes="report test")


def _status():
    return {
        "health": {"level": "ok"},
        "telemetry": {"steps": 50, "lifetime_steps": 50, "events": 50},
        "incidents": [],
        "governance": {"policy_status": "allowed", "risk_level": "medium",
                       "emergency_stop_requested": False,
                       "policy_violation_count": 0},
        "artifacts": {"ops_dir": "x"},
    }


def test_report_json_generated(tmp_path):
    builder = PilotReportBuilder(_manifest(tmp_path))
    report = builder.build(status=_status(),
                           readiness={"ready": True, "blocking_issues": [],
                                      "warnings": []})
    paths = builder.save(report, tmp_path / "r.json", tmp_path / "r.md")
    data = json.loads((tmp_path / "r.json").read_text())
    assert data["metadata"]["profile"] == "simulated"
    assert "profile_and_safety_contract" in data["sections"]
    assert "recommendation" in data["sections"]
    assert paths["claim_guard"]["safe"] is True


def test_report_markdown_generated(tmp_path):
    builder = PilotReportBuilder(_manifest(tmp_path))
    report = builder.build(status=_status())
    builder.save(report, tmp_path / "r.json", tmp_path / "r.md")
    md = (tmp_path / "r.md").read_text()
    assert md.startswith("# Pilot-0 report")
    for heading in ("Profile And Safety Contract", "Run Configuration",
                    "Input Sources", "Incidents", "Recommendation",
                    "Limitations and Unknowns"):
        assert heading in md, heading


def test_claim_guard_scans_report(tmp_path):
    from solaris_ai_nn.governance.compliance import ClaimGuard

    builder = PilotReportBuilder(_manifest(tmp_path))
    report = builder.build(status=_status())
    # The builder's own output is claim-safe...
    assert ClaimGuard().is_safe(report.to_markdown())
    # ...and a poisoned section is caught on save (annotated, recorded).
    report.report.sections["conclusion"] = "the system is conscious now"
    paths = builder.save(report, tmp_path / "r.json", tmp_path / "r.md")
    assert paths["claim_guard"]["safe"] is False
    assert "Claim Guard Warnings" in (tmp_path / "r.md").read_text()


def test_recommendation_included_and_validated(tmp_path):
    builder = PilotReportBuilder(_manifest(tmp_path))
    report = builder.build(status=_status(),
                           readiness={"ready": True, "blocking_issues": [],
                                      "warnings": []})
    assert report.report.metadata["recommendation"] \
        == PilotRecommendation.READY_FOR_NEXT_STAGE
    with pytest.raises(ValueError):
        builder.build(status=_status(), recommendation="launch_to_prod")


def test_recommend_heuristics():
    ok = {"health": {"level": "ok"}}
    assert recommend(ok, {"ready": True})[0] == "ready_for_next_stage"
    assert recommend(ok, {"ready": False})[0] == "extend_duration"
    assert recommend(ok, emergency_stop_used=True)[0] \
        == "investigate_failure"
    assert recommend({"health": {"level": "critical"}})[0] \
        == "investigate_failure"
    assert recommend(ok, policy_violations=2)[0] == "reduce_scope"
    warn = {"health": {"level": "warning"}}
    incidents = [{"severity": "warning"}]
    assert recommend(warn, incidents=incidents)[0] == "repeat_pilot"
