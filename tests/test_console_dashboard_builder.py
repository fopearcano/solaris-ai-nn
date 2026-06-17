"""Console dashboard builder: built, required sections, missing visible, no claims."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def test_dashboard_built(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    assert rt.dashboard is not None
    assert rt.dashboard.sections


def test_required_sections_present(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    s = rt.dashboard.sections
    for key in ("release_status", "quick_safety_status", "latest_fixture_run",
                "environmental_membrane", "quarantine_and_safety_blocks",
                "next_recommended_action", "missing_artifacts",
                "skipped_optional_stages", "limitations"):
        assert key in s, key


def test_missing_artifacts_visible(tmp_path):
    rt = build_console(tmp_path)  # empty
    assert rt.dashboard.sections["missing_artifacts"]


def test_no_unsupported_claims(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    text = " ".join(rt.dashboard.to_dict()["what_this_console_cannot_do"])
    assert ClaimGuard().scan_text(text).safe
    assert "consciousness" in text.lower()
