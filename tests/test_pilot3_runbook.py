"""Pilot3RunbookBuilder: renders an operator runbook; forbids real-world use."""

from __future__ import annotations

import os

from solaris_ai_nn.motor_membrane.operator_runbook import (
    ALLOWED,
    FORBIDDEN,
    WARNINGS,
    Pilot3RunbookBuilder,
)


def test_runbook_renders_sections():
    text = Pilot3RunbookBuilder().render().lower()
    assert "pilot-3" in text
    assert "actuation firewall" in text
    assert "dry-run" in text


def test_runbook_lists_forbidden_real_world():
    text = Pilot3RunbookBuilder().render().lower()
    assert "real-world actuation" in text
    for item in ("robot", "browser", "network"):
        assert item in text


def test_warnings_forbid_devices_and_claims():
    joined = " ".join(WARNINGS).lower()
    assert "robot" in joined or "device" in joined
    assert "consciousness" in joined


def test_allowed_is_simulation_only():
    joined = " ".join(ALLOWED).lower()
    assert "simulated" in joined or "dry-run" in joined
    assert "real" not in joined.replace("real-world", "")


def test_forbidden_covers_real_world_classes():
    joined = " ".join(FORBIDDEN).lower()
    for item in ("real-world", "device", "browser", "network", "command"):
        assert item in joined


def test_write_emits_markdown(tmp_path):
    path = Pilot3RunbookBuilder(base_dir=str(tmp_path)).write()
    assert os.path.exists(path)
    assert path.endswith("OPERATOR_RUNBOOK.md")
