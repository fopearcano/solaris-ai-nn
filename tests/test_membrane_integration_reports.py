"""Integration reports: disclaimers present, ClaimGuard-safe, raw-events-not-perception."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def _report(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0")
    rt.run()
    base = os.path.join(state, "membrane", "integration")
    return base, open(os.path.join(
        base, "MEMBRANE_INTEGRATION_REPORT.md")).read()


def test_main_report_has_disclaimer(tmp_path):
    _base, md = _report(tmp_path)
    assert "What this does NOT do" in md
    assert "audit material" in md
    assert "does NOT" in md or "not start" in md.lower()


def test_main_report_claimguard_safe(tmp_path):
    _base, md = _report(tmp_path)
    assert ClaimGuard().scan_text(md).safe


def test_sub_reports_claimguard_safe(tmp_path):
    base, _md = _report(tmp_path)
    for name in ("MEMBRANE_DOWNSTREAM_CONTRACTS.md", "MEMBRANE_BYPASS_REPORT.md",
                 "MEMBRANE_ANCESTRY_REPORT.md", "MEMBRANE_PIPELINE_AUDIT.md",
                 "MEMBRANE_INTEGRATION_SAFETY_REPORT.md"):
        text = open(os.path.join(base, name)).read()
        assert ClaimGuard().scan_text(text).safe, name


def test_reports_state_raw_events_not_perception(tmp_path):
    base, md = _report(tmp_path)
    contracts = open(os.path.join(
        base, "MEMBRANE_DOWNSTREAM_CONTRACTS.md")).read()
    combined = (md + contracts).lower()
    assert "raw events" in combined
    assert "impression" in combined
