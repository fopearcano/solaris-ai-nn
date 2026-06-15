"""Desire: memory stores traces; latent replay rec; Conscience phase exists."""

from __future__ import annotations

import os

from solaris_ai_nn.conscience.spine import SpinePhase
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _runtime(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=2)
    rt.run_bounded()
    return rt


def test_memory_stores_desire_traces(tmp_path):
    rt = _runtime(tmp_path)
    assert os.path.isfile(tmp_path / "d" / "desires.jsonl")
    assert os.path.isfile(tmp_path / "d" / "valence.jsonl")
    assert os.path.isfile(tmp_path / "d" / "desire_index.json")


def test_latent_replay_recommendation_exists(tmp_path):
    rt = _runtime(tmp_path)
    recs = rt.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6


def test_conscience_phase_exists():
    assert SpinePhase.DESIRE_FORMATION_UPDATE == "desire_formation_update"
    assert SpinePhase.DESIRE_FORMATION_UPDATE in SpinePhase.ORDER
    assert SpinePhase.SAFE_INTERNAL_ACTION_ARBITRATION in SpinePhase.ORDER
    order = SpinePhase.ORDER
    assert order.index(SpinePhase.PERCEPTUAL_METABOLISM_UPDATE) \
        < order.index(SpinePhase.DESIRE_FORMATION_UPDATE) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def test_conscience_profiles_exist():
    from solaris_ai_nn.conscience.scenario_profiles import \
        ScenarioProfileRegistry

    reg = ScenarioProfileRegistry()
    for pid in ("desire_formation_fixture_short", "desire_conflict_demo",
                "internal_action_readiness_demo", "no_action_arbitration_demo",
                "safety_blocked_desire_demo", "desire_formation_report_only"):
        assert reg.get(pid) is not None
