"""Clean-machine check: checklist generated, hidden-path/live-state/service blockers."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import CleanMachineReadinessCheck
from solaris_ai_nn.tester_packaging.clean_machine_check import (
    CleanMachineChecklistItem,
    CleanMachineReadinessResult,
)


def test_clean_machine_checklist_generated():
    result = CleanMachineReadinessCheck().check()
    assert result.checklist.items
    d = result.to_dict()
    assert d["report_only"] is True


def test_hidden_local_path_blocker():
    r = CleanMachineReadinessResult()
    r.checklist.items.append(CleanMachineChecklistItem(
        "no_dependency_on_developer_machine", satisfied=False, required=True))
    assert r.passed is False
    assert "no_dependency_on_developer_machine" in [i.check for i in r.blockers]


def test_live_state_dependency_blocker():
    r = CleanMachineReadinessResult()
    r.checklist.items.append(CleanMachineChecklistItem(
        "fixture_demo_does_not_require_live_state", satisfied=False,
        required=True))
    assert r.passed is False


def test_external_service_dependency_warning():
    r = CleanMachineReadinessResult()
    r.checklist.items.append(CleanMachineChecklistItem(
        "no_dependency_on_external_services", satisfied=False, required=False))
    # Optional service-dependency note is a warning, not a hard blocker here.
    assert r.passed is True
    assert r.warnings


def test_repo_fixture_self_contained():
    # In this repo the fixture demo is self-contained (no live state needed).
    result = CleanMachineReadinessCheck().check()
    item = next(i for i in result.checklist.items
                if i.check == "fixture_demo_does_not_require_live_state")
    assert item.satisfied is True
