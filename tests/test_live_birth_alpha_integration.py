"""Live birth <-> Alpha: live profile registered, default fixture-only, gated."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.alpha_system.alpha_profile import (
    available_profiles,
    default_alpha_profile,
    get_alpha_profile,
)
from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    governance_template,
)


def test_live_profile_registered():
    assert "live_readonly_birth_v0" in available_profiles()


def test_default_alpha_remains_fixture_only():
    p = default_alpha_profile()
    assert p.is_fixture_only is True
    # Asking the alpha layer for the live profile still returns fixture-only.
    live = get_alpha_profile("live_readonly_birth_v0")
    assert live.is_fixture_only is True
    assert any("live_readonly_birth_v0" in l for l in live.limitations)


def test_live_profile_blocked_without_governance(tmp_path):
    rt = LiveReadOnlyBirthRuntime(state_dir=str(tmp_path),
                                  require_governance=True)
    rt.initialize()
    # Write SAFE-OFF governance (disabled/unapproved).
    with open(os.path.join(str(tmp_path), "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(governance_template(), fh)
    result = LiveReadOnlyBirthRuntime(
        state_dir=str(tmp_path), require_governance=True).run()
    assert result["blocked"] is True
