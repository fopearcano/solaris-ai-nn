"""First tester acceptance criteria: generated, install/fixture/console/claims."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    AcceptanceCategory,
    FirstTesterAcceptanceCriteria,
)


def test_criteria_generated(tmp_path):
    path = FirstTesterAcceptanceCriteria().write(str(tmp_path))
    text = open(path, encoding="utf-8").read()
    assert "First Tester Acceptance Criteria" in text


def test_install_criteria_present():
    c = FirstTesterAcceptanceCriteria()
    assert c.by_category(AcceptanceCategory.INSTALL)


def test_fixture_criteria_present():
    c = FirstTesterAcceptanceCriteria()
    items = c.by_category(AcceptanceCategory.FIXTURE_DEMO)
    assert items
    assert any("quarantine" in i.text for i in items)


def test_console_criteria_present():
    c = FirstTesterAcceptanceCriteria()
    items = c.by_category(AcceptanceCategory.CONSOLE)
    assert any("read-only" in i.text for i in items)


def test_claims_criteria_present():
    c = FirstTesterAcceptanceCriteria()
    items = c.by_category(AcceptanceCategory.CLAIMS)
    text = " ".join(i.text for i in items).lower()
    assert "consciousness" in text
    assert "perception" in text
