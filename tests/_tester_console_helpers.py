"""Shared helpers for tester console tests (not a test module)."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def stage_fixture(tester_state_dir):
    """Run a real fixture tester demo so the console has artifacts."""
    TesterFixtureDemoRuntime(state_dir=tester_state_dir,
                             profile="fixture_tester_v0").run()
    return tester_state_dir


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def stage_membrane_bypass(live_dir):
    write_json(os.path.join(live_dir, "membrane", "integration",
                            "MEMBRANE_INTEGRATION_REPORT.json"),
               {"sections": {"status": {"critical_bypass_count": 2,
                                        "raw_fallback_count": 1}}})


def stage_quarantine(live_dir, count=3):
    write_json(os.path.join(live_dir, "quarantine", "q.json"),
               {"quarantined_count": count})


def stage_forbidden_governance(live_dir):
    write_json(os.path.join(live_dir, "governance",
                            "LIVE_READONLY_GOVERNANCE.json"),
               {"live_readonly_enabled": True, "operator_approved": True,
                "allowed_sources": ["chronos_absence", "raw_microphone"],
                "forbidden_sources": ["raw_microphone"], "rules": {}})


def stage_claim(claims_dir):
    write_json(os.path.join(claims_dir, "claim.json"),
               {"forbidden_claim_count": 1, "unsupported_claim_count": 1})


def build_console(tmp_path, *, fixture=False, html=False, **kwargs):
    base = str(tmp_path)
    live = os.path.join(base, "live")
    tester = os.path.join(base, "tester")
    if fixture:
        stage_fixture(tester)
    rt = TesterConsoleRuntime(
        state_dir=live, tester_state_dir=tester,
        console_dir=os.path.join(base, "console"), html=html, **kwargs)
    rt.run()
    return rt
