"""Pilot-1 operator runbook: generation, emergency procedure, warnings."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot1 import OperatorRunbookBuilder, PilotConfig


def test_runbook_generated(tmp_path):
    path = OperatorRunbookBuilder(base_dir=str(tmp_path)).write(
        PilotConfig(base_dir=str(tmp_path)))
    assert os.path.exists(path)
    assert os.path.basename(path) == "OPERATOR_RUNBOOK.md"


def test_emergency_stop_procedure_included(tmp_path):
    text = OperatorRunbookBuilder(base_dir=str(tmp_path)).render(
        PilotConfig(base_dir=str(tmp_path)))
    assert "Emergency stop procedure" in text
    assert "EMERGENCY_STOP" in text


def test_warnings_included(tmp_path):
    text = OperatorRunbookBuilder(base_dir=str(tmp_path)).render(
        PilotConfig(base_dir=str(tmp_path)))
    for fragment in ("Do not call a simulated month a real month",
                     "Do not enable real-world actuation",
                     "Do not disable the emergency stop",
                     "consciousness"):
        assert fragment in text


def test_phases_documented(tmp_path):
    text = OperatorRunbookBuilder(base_dir=str(tmp_path)).render(
        PilotConfig(base_dir=str(tmp_path)))
    for section in ("plan-only mode", "24h real soak", "7d real soak",
                    "30d real soak", "post-run analysis"):
        assert section.lower() in text.lower()
