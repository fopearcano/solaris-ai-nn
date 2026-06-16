"""Live governance: missing blocks, unapproved blocks, control blocks, forbidden."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import (
    GovernanceStatus,
    GovernanceValidator,
    approved_governance,
    governance_template,
)


def _load(tmp_path, gov=None):
    state = str(tmp_path)
    if gov is not None:
        os.makedirs(os.path.join(state, "governance"), exist_ok=True)
        with open(os.path.join(state, "governance",
                               "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
            json.dump(gov, fh)
    v = GovernanceValidator()
    return v.validate(v.load(state))


def test_missing_governance_blocks(tmp_path):
    result = _load(tmp_path, gov=None)
    assert result["governance_passed"] is False
    assert result["governance_status"] == GovernanceStatus.MISSING


def test_operator_approved_false_blocks(tmp_path):
    result = _load(tmp_path, gov=governance_template())  # SAFE-OFF
    assert result["governance_passed"] is False
    assert any("operator_approved" in b or "live_readonly_enabled" in b
               for b in result["blockers"])


def test_solaris_control_permission_blocks(tmp_path):
    gov = approved_governance()
    gov["rules"]["solaris_may_start_feeders"] = True
    result = _load(tmp_path, gov=gov)
    assert result["governance_passed"] is False
    assert result["governance_status"] == GovernanceStatus.CONTROL_GRANTED


def test_forbidden_source_in_allowed_blocks(tmp_path):
    gov = approved_governance()
    gov["allowed_sources"] = gov["allowed_sources"] + ["raw_camera"]
    result = _load(tmp_path, gov=gov)
    assert result["governance_passed"] is False
    assert result["governance_status"] == \
        GovernanceStatus.FORBIDDEN_SOURCE_ALLOWED


def test_approved_governance_passes(tmp_path):
    result = _load(tmp_path, gov=approved_governance())
    assert result["governance_passed"] is True
    assert result["governance_status"] == GovernanceStatus.PASS
