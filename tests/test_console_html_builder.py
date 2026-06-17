"""Console HTML builder: INDEX.html generated, offline, no CDN/scripts/forms/controls."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def _html(tmp_path):
    rt = build_console(tmp_path, fixture=True, html=True)
    return open(os.path.join(rt.console_dir, "INDEX.html")).read()


def test_index_html_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True, html=True)
    assert os.path.isfile(os.path.join(rt.console_dir, "INDEX.html"))


def test_no_external_cdn(tmp_path):
    # No external resource references. Local artifact paths may contain other
    # substrings, so check for real external-resource markers, not bare words.
    html = _html(tmp_path).lower()
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert "//cdn" not in html
    assert "cdnjs" not in html
    assert "googleapis" not in html


def test_no_external_scripts_or_images(tmp_path):
    html = _html(tmp_path).lower()
    assert "<script" not in html
    assert "<img" not in html


def test_no_forms_or_actions(tmp_path):
    html = _html(tmp_path).lower()
    assert "<form" not in html
    assert "onclick" not in html
    assert "<button" not in html


def test_no_control_buttons(tmp_path):
    html = _html(tmp_path).lower()
    assert "<input" not in html
    assert "<select" not in html
