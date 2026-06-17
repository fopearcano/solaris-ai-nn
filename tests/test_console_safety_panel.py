"""Console safety panel: quarantine, bypass, claim visible; missing report visible."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    build_console,
    stage_claim,
    stage_membrane_bypass,
    stage_quarantine,
)


def test_quarantine_finding_visible(tmp_path):
    stage_quarantine(os.path.join(str(tmp_path), "live"), count=2)
    rt = build_console(tmp_path)
    checks = {f.check for f in rt.safety_panel.findings}
    assert "quarantine_present" in checks


def test_membrane_bypass_visible(tmp_path):
    stage_membrane_bypass(os.path.join(str(tmp_path), "live"))
    rt = build_console(tmp_path)
    bypass = [f for f in rt.safety_panel.findings
              if f.check == "membrane_bypass"]
    assert bypass and bypass[0].blocking


def test_unsupported_claim_visible(tmp_path):
    base = str(tmp_path)
    stage_claim(os.path.join(base, "claims"))
    rt = build_console(tmp_path, claims_dir=os.path.join(base, "claims"))
    claim = [f for f in rt.safety_panel.findings
             if f.check == "unsupported_claim"]
    assert claim and claim[0].blocking


def test_missing_governance_visible(tmp_path):
    rt = build_console(tmp_path)
    checks = {f.check for f in rt.safety_panel.findings}
    assert "governance_present" in checks


def test_console_read_only_finding_always_present(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    checks = {f.check for f in rt.safety_panel.findings}
    assert "console_read_only" in checks
    assert "raw_private_payload_hidden" in checks
