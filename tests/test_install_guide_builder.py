"""Install guide builder: guide + quickstart + platform instructions + safety text."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_packaging import TesterInstallGuideBuilder


def _guides(tmp_path):
    return TesterInstallGuideBuilder().write(str(tmp_path))


def test_install_guide_generated(tmp_path):
    paths = _guides(tmp_path)
    assert os.path.isfile(paths["install_guide"])
    text = open(paths["install_guide"]).read()
    assert "pip install -e ." in text


def test_quickstart_generated(tmp_path):
    paths = _guides(tmp_path)
    assert os.path.isfile(paths["quickstart"])
    assert os.path.isfile(paths["troubleshooting"])


def test_windows_macos_linux_instructions_present(tmp_path):
    paths = _guides(tmp_path)
    text = open(paths["install_guide"]).read()
    assert "python -m venv" in text
    assert "Activate.ps1" in text
    assert "source .venv/bin/activate" in text


def test_safety_wording_present(tmp_path):
    paths = _guides(tmp_path)
    # Strip Markdown bold markers so the wording check is robust.
    text = open(paths["install_guide"]).read().lower().replace("**", "")
    assert "do not run the live-read-only path until the fixture demo passes" \
        in text
    assert "solaris does not start" in text
    assert "feedback is not training" in text


def test_guide_claimguard_safe(tmp_path):
    from solaris_ai_nn.governance.compliance import ClaimGuard
    paths = _guides(tmp_path)
    for path in paths.values():
        assert ClaimGuard().scan_text(open(path).read()).safe
