"""Integration: ecology pressure reaches latent, homeostasis, executive."""

from __future__ import annotations

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_absence_rate_becomes_low_stimulus_pressure(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path / "h"))
    result = regulator.update({"ecology": {"absence_rate": 0.4,
                                           "anomaly_rate": 0.0,
                                           "novelty_rate": 0.0}})
    assert regulator.state.value("low_stimulus_pressure", 0.0) > 0.0
    assert result is not None


def test_anomaly_novelty_become_unknown_pressure(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path / "h"))
    regulator.update({"ecology": {"absence_rate": 0.0,
                                  "anomaly_rate": 0.2,
                                  "novelty_rate": 0.2}})
    assert regulator.state.value("unknown_pressure", 0.0) > 0.0
    assert regulator.state.value("novelty_pressure", 0.0) > 0.0


def test_scarcity_pressures_feed_homeostasis(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path / "h"))
    regulator.update({"ecology": {
        "absence_rate": 0.0, "anomaly_rate": 0.0, "novelty_rate": 0.0,
        "scarcity_pressures": {"seek_signal_pressure": 0.8,
                               "rest_consolidation_pressure": 0.6}}})
    assert regulator.state.value("low_stimulus_pressure", 0.0) >= 0.8
    assert regulator.state.value("fatigue", 0.0) >= 0.6


def test_danger_active_raises_danger_proximity(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path / "h"))
    regulator.update({"ecology": {
        "absence_rate": 0.0, "anomaly_rate": 0.0, "novelty_rate": 0.0,
        "danger_active": True}})
    assert regulator.state.value("danger_proximity", 0.0) >= 0.7


def test_silent_world_produces_latent_activation_opportunity(tmp_path):
    # A silence-heavy nursery returns None on many steps; the runner's own
    # absence machinery (latent) then activates. Here we assert the provider
    # actually yields the quiet steps that make that possible.
    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=120, absence_rate=0.7,
        active_regimes=[RegimeType.LONG_SILENCE],
        output_state_dir=str(tmp_path / "eco")))
    nones = sum(1 for step in range(120)
                if nursery.stimulus_provider(step) is None)
    assert nones > 10
