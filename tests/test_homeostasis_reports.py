"""Tests for homeostasis reports."""

from __future__ import annotations

import json

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.homeostasis.reports import HomeostasisReportBuilder


def _regulator(tmp_path):
    regulator = HomeostaticRegulator(state_dir=tmp_path)
    regulator.update({
        "embodiment": {"energy": 1.0, "max_energy": 10.0,
                       "exhausted": True, "dist_danger": 1.0,
                       "dist_reward": 1.0},
        "latent": {"mysterium_pressure": 0.8,
                   "anticipation_accuracy": 0.4},
        "valence_events": [{"kind": "reaction", "value": -0.5}],
    })
    return regulator


def test_report_json_generated(tmp_path):
    builder = HomeostasisReportBuilder(_regulator(tmp_path))
    data = json.loads(builder.to_json())
    for section in ("homeostatic_variables", "dominant_needs",
                    "drive_pressures", "valence_trend",
                    "being_not_being_tension", "conflicts",
                    "desire_candidates", "suppressed_desires",
                    "safety_governance_decisions"):
        assert section in data["sections"], section


def test_markdown_generated_with_limitations(tmp_path):
    md = HomeostasisReportBuilder(_regulator(tmp_path)).to_markdown()
    assert md.startswith("# Homeostasis report")
    assert "Limitations and Unknowns" in md
    assert "not commands, wants, or feelings" in md
    assert "feedback polarity" in md
    assert "No claim of will, free agency, or consciousness" in md


def test_claim_guard_scans_report(tmp_path):
    builder = HomeostasisReportBuilder(_regulator(tmp_path))
    paths = builder.save(tmp_path / "h.json", tmp_path / "h.md")
    assert paths["claim_guard"]["safe"] is True
    assert paths["anthropomorphism_check"]["safe"] is True
    assert (tmp_path / "h.md").exists()


def test_no_anthropomorphic_claims(tmp_path):
    md = HomeostasisReportBuilder(_regulator(tmp_path)).to_markdown()
    assert ClaimGuard().is_safe(md)
    lowered = md.lower()
    for forbidden in ("the system wants", "the system wanted",
                      "the system feels", "the system felt",
                      "is happy", "is sad"):
        assert forbidden not in lowered, forbidden
