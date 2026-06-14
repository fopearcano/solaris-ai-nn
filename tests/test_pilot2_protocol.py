"""Pilot-2 protocol: phases, gating, persistence."""

from __future__ import annotations

from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.pilot2 import (
    Pilot2Config,
    Pilot2Mode,
    Pilot2Phase,
    Pilot2PhaseStatus,
    Pilot2Protocol,
)


def _proto(tmp_path, governance=None):
    cfg = Pilot2Config(mode=Pilot2Mode.PLAN_ONLY, base_dir=str(tmp_path))
    return Pilot2Protocol(config=cfg, governance=governance)


def test_phases_exist():
    for p in ("plan_only", "source_preflight", "membrane_dry_run",
              "fixture_short_run", "nursery_baseline_run",
              "mixed_nursery_membrane_run", "read_only_24h_soak",
              "read_only_7d_soak", "read_only_30d_soak",
              "comparative_analysis", "post_run_archive"):
        assert p in Pilot2Phase.ORDER


def test_real_30d_blocked_without_governance(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(Pilot2Phase.SOURCE_PREFLIGHT)
    proto.complete_phase(Pilot2Phase.SOURCE_PREFLIGHT, True)
    proto.complete_phase(Pilot2Phase.MEMBRANE_DRY_RUN, True)
    out = proto.enter_phase(Pilot2Phase.READ_ONLY_30D_SOAK)
    assert out.get("blocked") is True


def test_real_30d_allowed_with_governance(tmp_path):
    gov = GovernancePolicy()
    gov.permissions.grant("enable_pilot2_real_read_only_30d")
    proto = _proto(tmp_path, governance=gov)
    proto.complete_phase(Pilot2Phase.SOURCE_PREFLIGHT, True)
    proto.complete_phase(Pilot2Phase.MEMBRANE_DRY_RUN, True)
    out = proto.enter_phase(Pilot2Phase.READ_ONLY_30D_SOAK)
    assert out["entered"] is True


def test_state_persists(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(Pilot2Phase.SOURCE_PREFLIGHT)
    proto.complete_phase(Pilot2Phase.SOURCE_PREFLIGHT, True)
    cfg = Pilot2Config(mode=Pilot2Mode.PLAN_ONLY, base_dir=str(tmp_path))
    reborn = Pilot2Protocol(config=cfg)
    assert reborn.state.preflight_passed is True
    assert (tmp_path / "pilot2_phase_history.jsonl").exists()


def test_failed_phase_writes_report(tmp_path):
    proto = _proto(tmp_path)
    out = proto.complete_phase(Pilot2Phase.SOURCE_PREFLIGHT, False, "bad src")
    assert out["failure_report"]
    assert proto.state.failure_reports
