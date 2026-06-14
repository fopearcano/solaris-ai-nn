"""Pilot3SoakRunbookBuilder: runbook generated, forbidden listed, Pilot-4 note."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot3.operator_runbook import (
    ALLOWED,
    FORBIDDEN,
    WARNINGS,
    Pilot3SoakRunbookBuilder,
)


def test_runbook_generated(tmp_path):
    path = Pilot3SoakRunbookBuilder(base_dir=str(tmp_path)).write()
    assert os.path.exists(path) and path.endswith("OPERATOR_RUNBOOK.md")


def test_forbidden_actions_listed():
    text = Pilot3SoakRunbookBuilder().render().lower()
    assert "what is forbidden" in text
    joined = " ".join(FORBIDDEN).lower()
    for item in ("real-world actuation", "network", "device", "robot"):
        assert item in joined


def test_pilot4_planning_only_warning_included():
    text = Pilot3SoakRunbookBuilder().render().lower()
    assert "future pilot-4 is planning-only" in text
    assert "real-world actuation is not permitted" in text


def test_warnings_and_allowed():
    joined_w = " ".join(WARNINGS).lower()
    assert "do not connect real actuators" in joined_w
    assert "do not claim consciousness" in joined_w
    joined_a = " ".join(ALLOWED).lower()
    assert "sandbox" in joined_a or "dry-run" in joined_a


def test_non_actuation_verification_section():
    text = Pilot3SoakRunbookBuilder().render().lower()
    assert "how to verify non-actuation" in text
