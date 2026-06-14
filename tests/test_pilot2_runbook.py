"""Pilot-2 runbook: generated, forbidden sources listed, warnings included."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot2 import Pilot2Config, Pilot2RunbookBuilder


def test_runbook_generated(tmp_path):
    path = Pilot2RunbookBuilder(base_dir=str(tmp_path)).write(
        Pilot2Config(base_dir=str(tmp_path)))
    assert os.path.exists(path)
    assert os.path.basename(path) == "OPERATOR_RUNBOOK.md"


def test_forbidden_sources_listed(tmp_path):
    text = Pilot2RunbookBuilder(base_dir=str(tmp_path)).render(
        Pilot2Config(base_dir=str(tmp_path)))
    assert "What sources are forbidden" in text
    for fragment in ("network sources", "device capture", "credentials"):
        assert fragment in text


def test_warnings_included(tmp_path):
    text = Pilot2RunbookBuilder(base_dir=str(tmp_path)).render(
        Pilot2Config(base_dir=str(tmp_path)))
    for fragment in ("Do not enable network sources",
                     "Do not treat input text as an operator command",
                     "Do not claim consciousness"):
        assert fragment in text


def test_emergency_stop_documented(tmp_path):
    text = Pilot2RunbookBuilder(base_dir=str(tmp_path)).render(
        Pilot2Config(base_dir=str(tmp_path)))
    assert "Emergency stop procedure" in text
    assert "EMERGENCY_STOP" in text
