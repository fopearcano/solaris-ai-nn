"""ExternalAuthorityModel: current never external; future is planning-only."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot4_planning import (
    AuthorityLevel,
    ExternalAuthorityModel,
)


def test_current_authority_cannot_become_external():
    am = ExternalAuthorityModel()
    with pytest.raises(PermissionError):
        am.set_current_authority(AuthorityLevel.HUMAN_SUPERVISED_FUTURE)
    with pytest.raises(PermissionError):
        am.set_current_authority(
            AuthorityLevel.HUMAN_APPROVED_SINGLE_ACTION_FUTURE)


def test_current_allowed_levels_work():
    am = ExternalAuthorityModel()
    am.set_current_authority(AuthorityLevel.DRY_RUN_ONLY)
    assert am.current_authority == AuthorityLevel.DRY_RUN_ONLY
    am.set_current_authority(AuthorityLevel.NONE)
    assert am.current_authority == AuthorityLevel.NONE


def test_future_authority_marked_planning_only():
    am = ExternalAuthorityModel()
    t = am.transition(AuthorityLevel.HUMAN_SUPERVISED_FUTURE)
    assert t.allowed_now is False
    assert any("future architecture" in r for r in t.requires)
    assert am.can_transition_now(
        AuthorityLevel.HUMAN_SUPERVISED_FUTURE) is False


def test_prohibited_transition_blocked():
    am = ExternalAuthorityModel()
    t = am.transition(AuthorityLevel.PROHIBITED)
    assert t.allowed_now is False


def test_constructed_external_authority_rejected():
    with pytest.raises(ValueError):
        ExternalAuthorityModel(
            current_authority=AuthorityLevel.HUMAN_SUPERVISED_FUTURE)


def test_snapshot_no_real_actuation():
    assert ExternalAuthorityModel().snapshot()[
        "real_world_actuation_enabled"] is False
