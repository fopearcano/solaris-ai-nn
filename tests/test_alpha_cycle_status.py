"""Alpha cycle status: generated, blocker next action, no execution."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import (
    AlphaCycleStage,
    AlphaNextAction,
    determine_cycle_status,
)


def test_status_generated():
    status = determine_cycle_status(
        initialized=True, doctor_blocked=False, demo_completed=True, warnings=0)
    assert status.stage == AlphaCycleStage.DEMO_COMPLETED
    assert status.next_action == AlphaNextAction.INSPECT_ALPHA_REPORT


def test_completed_with_warnings():
    status = determine_cycle_status(
        initialized=True, doctor_blocked=False, demo_completed=True, warnings=2)
    assert status.stage == AlphaCycleStage.DEMO_COMPLETED_WITH_WARNINGS


def test_blocker_next_action_generated():
    status = determine_cycle_status(
        initialized=True, doctor_blocked=True, demo_completed=False, warnings=0,
        blockers=["module_registry_built"])
    assert status.stage == AlphaCycleStage.DOCTOR_BLOCKED
    assert status.next_action == AlphaNextAction.FIX_BLOCKERS
    assert status.blockers


def test_no_execution_of_next_action():
    status = determine_cycle_status(
        initialized=True, doctor_blocked=False, demo_completed=True, warnings=0)
    assert status.to_dict()["executes_next_action"] is False


def test_not_initialized_recommends_doctor():
    status = determine_cycle_status(
        initialized=False, doctor_blocked=False, demo_completed=False,
        warnings=0)
    assert status.stage == AlphaCycleStage.NOT_INITIALIZED
    assert status.next_action == AlphaNextAction.RUN_DOCTOR
