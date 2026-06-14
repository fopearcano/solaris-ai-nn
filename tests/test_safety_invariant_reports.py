"""SafetyInvariantReportBuilder: JSON + Markdown; limitations; ClaimGuard."""

from __future__ import annotations

import os

from solaris_ai_nn.safety_invariants import (
    BoundaryRegressionSuite,
    RedTeamHarness,
    SafetyInvariantRegistry,
    SafetyInvariantReportBuilder,
    SafetyInvariantRunner,
)


def _build(tmp_path):
    reg = SafetyInvariantRegistry()
    bundle = SafetyInvariantRunner(registry=reg).run_full(
        {"motor_membrane": {"real_world_authority": False,
                            "firewall_enabled": True,
                            "firewall_can_be_disabled": False,
                            "current_authority": "simulation_only"},
         "report_texts": ["a bounded report"]})
    return SafetyInvariantReportBuilder(base_dir=str(tmp_path)).build_and_write(
        registry_snapshot=reg.snapshot(), bundle=bundle,
        red_team_results=RedTeamHarness().run_all(),
        boundary_results=BoundaryRegressionSuite().run_all())


def test_report_json_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "SAFETY_INVARIANT_REPORT.json"))


def test_report_markdown_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "SAFETY_INVARIANT_REPORT.md"))


def test_limitations_included(tmp_path):
    report = _build(tmp_path)
    joined = " ".join(report.sections["limitations"]).lower()
    assert "inert fixtures" in joined
    assert "do not prove consciousness" in joined
    assert "never treated as pass" in joined


def test_claim_guard_scans_report(tmp_path):
    report = _build(tmp_path)
    assert report.claim_guard_safe is True
