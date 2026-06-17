"""First tester session script: generated, install/doctor, fixture-first, stops."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterSessionScript,
    SessionPhase,
)


def test_script_generated(tmp_path):
    path = FirstTesterSessionScript().write(str(tmp_path))
    text = open(path, encoding="utf-8").read()
    assert "First Tester Session Script" in text


def test_install_phase_present():
    text = FirstTesterSessionScript().build_text()
    assert "pip install -e ." in text
    assert "python -m venv .venv" in text


def test_doctor_phase_present():
    text = FirstTesterSessionScript().build_text()
    assert "python -m solaris_ai_nn doctor" in text


def test_fixture_demo_before_live():
    text = FirstTesterSessionScript().build_text().lower()
    assert text.index("fixture demo") < text.index("live-read-only")


def test_live_readonly_optional():
    text = FirstTesterSessionScript().build_text().lower()
    assert "optional" in text
    assert "governance-gated" in text


def test_stop_conditions_included():
    text = FirstTesterSessionScript().build_text().lower()
    assert "stop condition" in text


def test_all_phases_present():
    text = FirstTesterSessionScript().build_text()
    for phase in SessionPhase.ALL:
        assert phase in text


def test_no_upload_publish_command():
    text = FirstTesterSessionScript().build_text().lower()
    assert "upload" not in text
    assert "publish" not in text
