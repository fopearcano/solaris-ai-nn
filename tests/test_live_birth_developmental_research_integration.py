"""Live birth <-> Developmental/Research: next phases recommended, not executed."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
    governance_template,
)


def _run(tmp_path, gov):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(gov, fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    rt.run()
    return rt


def test_next_phases_recommended_not_executed(tmp_path):
    rt = _run(tmp_path, approved_governance())
    phases = rt.next_phase_recommendations()
    phase_ids = {p["phase"] for p in phases}
    assert "live_observation_2h" in phase_ids
    assert "live_short_developmental_soak_7_30d" in phase_ids
    # Recommendations are descriptive; the runtime started no phase.
    assert rt.live_birth_status()["starts_feeders"] is False


def test_blocked_birth_recommends_fix(tmp_path):
    rt = _run(tmp_path, governance_template())  # SAFE-OFF -> blocked
    phases = rt.next_phase_recommendations()
    assert any(p["phase"] == "fix_blockers" for p in phases)


def test_birth_status_is_cycle_evidence(tmp_path):
    rt = _run(tmp_path, approved_governance())
    st = rt.live_birth_status()
    # The status is recordable as research-cycle evidence (operational only).
    assert st["live_birth_enabled"] is True
    assert "governance_status" in st
