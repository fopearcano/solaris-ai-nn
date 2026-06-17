"""Console Markdown builder: INDEX.md + pages generated, read-only disclaimers."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def test_index_md_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    index = os.path.join(rt.console_dir, "INDEX.md")
    assert os.path.isfile(index)
    text = open(index).read()
    assert "# Solaris-AI-NN Tester Console" in text


def test_pages_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    pages = os.path.join(rt.console_dir, "pages")
    for name in ("SAFETY.md", "RUNS.md", "MEMBRANE.md", "QUARANTINE.md",
                 "FIXTURE.md", "LIVE.md", "CLAIMS.md", "NEXT_ACTIONS.md"):
        assert os.path.isfile(os.path.join(pages, name)), name


def test_read_only_disclaimers_present(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    text = open(os.path.join(rt.console_dir, "INDEX.md")).read().lower()
    assert "read-only" in text
    assert "does not start" in text
    assert "what this console cannot do" in text


def test_index_claimguard_safe(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    text = open(os.path.join(rt.console_dir, "INDEX.md")).read()
    assert ClaimGuard().scan_text(text).safe
