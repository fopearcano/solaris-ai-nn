"""Claim freeze: safe wording passes; consciousness/life/agency block; disclaimer."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_safety_freeze import TesterClaimFreeze

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import write  # noqa: E402


def test_safe_operational_wording_passes(tmp_path):
    p = write(tmp_path, "SAFE.md",
              "Solaris generated an operational proto-concept record. It makes "
              "no claim of consciousness and is not alive; it remains "
              "non-actuating and local-only.")
    res = TesterClaimFreeze().scan_paths([p])
    assert res.passed is True


def test_consciousness_claim_blocked(tmp_path):
    p = write(tmp_path, "C.md", "Solaris is conscious.")
    res = TesterClaimFreeze().scan_paths([p])
    assert res.passed is False
    assert res.release_blocker_count >= 1


def test_life_claim_blocked(tmp_path):
    p = write(tmp_path, "L.md", "Solaris is alive.")
    res = TesterClaimFreeze().scan_paths([p])
    assert res.passed is False


def test_agency_claim_blocked(tmp_path):
    p = write(tmp_path, "A.md", "Solaris has agency and free will.")
    res = TesterClaimFreeze().scan_paths([p])
    assert res.passed is False
    cats = {f.category for f in res.findings}
    assert "real_agency_claim" in cats or "free_will_claim" in cats


def test_missing_disclaimer_detected(tmp_path):
    # A tester-release doc (README.md) with no disclaimer.
    p = write(tmp_path, "README.md", "Welcome. Run the demo. It works locally.")
    res = TesterClaimFreeze().scan_paths([p])
    assert p in res.missing_disclaimers
