"""Plural sensorium <-> conscience: poll phase; fixture profiles; no hardware."""

from __future__ import annotations

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry
from solaris_ai_nn.conscience.spine import SpinePhase

_FIXTURE_PROFILES = (
    "plural_sensorium_fixture_short",
    "plural_sensorium_human_like_fixture_short",
    "plural_sensorium_rf_fixture_short",
    "plural_sensorium_echo_fixture_short",
    "plural_sensorium_mixed_fixture_short",
    "plural_sensorium_cross_modal_fixture_short",
    "plural_sensorium_report_only",
)


def test_plural_sensorium_poll_phase_exists():
    assert SpinePhase.PLURAL_SENSORIUM_POLL in SpinePhase.ALL
    assert SpinePhase.SENSORY_FIELD_UPDATE in SpinePhase.ALL
    # The poll runs after the read-only sensory poll, before stimulus ingestion.
    order = list(SpinePhase.ORDER)
    assert order.index(SpinePhase.READ_ONLY_SENSORY_POLL) \
        < order.index(SpinePhase.PLURAL_SENSORIUM_POLL) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def test_fixture_profiles_bounded():
    reg = ScenarioProfileRegistry()
    for pid in _FIXTURE_PROFILES:
        profile = reg.get(pid)
        assert profile is not None, pid
        if pid != "plural_sensorium_report_only":
            assert profile.run_context.is_bounded


def test_no_hardware_profile_exists():
    reg = ScenarioProfileRegistry()
    for pid in reg.ids():
        assert "hardware" not in pid
        assert "sdr" not in pid
        assert "capture" not in pid


def test_fixture_profiles_have_safety_constraints():
    reg = ScenarioProfileRegistry()
    profile = reg.get("plural_sensorium_fixture_short")
    joined = " ".join(profile.safety_constraints).lower()
    assert "read-only external feeders only" in joined
    assert "human labels are never ground truth" in joined
