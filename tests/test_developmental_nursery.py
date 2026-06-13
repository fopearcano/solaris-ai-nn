"""Tests for the DevelopmentalNursery (the world the system grows up in)."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ecology.nursery import (
    DevelopmentalNursery,
    NurseryConfig,
    NurseryState,
)
from solaris_ai_nn.ecology.regimes import RegimeType


def _nursery(tmp_path, **kw):
    config = NurseryConfig(seed=7, duration_steps=120,
                           output_state_dir=tmp_path, **kw)
    return DevelopmentalNursery(config=config)


def test_generate_step_returns_events(tmp_path):
    nursery = _nursery(tmp_path)
    saw_events = False
    for step in range(120):
        events = nursery.generate_step(step)
        if events:
            saw_events = True
        for event in events:
            assert event.stimulus.source == "developmental_nursery"
    assert saw_events
    assert nursery.memory.total_events() > 0


def test_stimulus_provider_absence_returns_none(tmp_path):
    nursery = _nursery(tmp_path, absence_rate=0.7,
                       active_regimes=[RegimeType.LONG_SILENCE])
    nones = sum(1 for step in range(120)
                if nursery.stimulus_provider(step) is None)
    # A silence-heavy world should produce some None (latent activation).
    assert nones > 0


def test_stimulus_provider_returns_canonical_signal(tmp_path):
    nursery = _nursery(tmp_path,
                       active_regimes=[RegimeType.STABLE_REPETITION])
    got_signal = False
    for step in range(120):
        signal = nursery.stimulus_provider(step)
        if signal is not None:
            got_signal = True
            assert signal.origin == "developmental_nursery"
    assert got_signal


def test_determinism_same_seed(tmp_path):
    a = DevelopmentalNursery(config=NurseryConfig(
        seed=11, duration_steps=80, output_state_dir=None))
    b = DevelopmentalNursery(config=NurseryConfig(
        seed=11, duration_steps=80, output_state_dir=None))
    for step in range(80):
        sa = a.stimulus_provider(step)
        sb = b.stimulus_provider(step)
        assert (sa is None) == (sb is None)
        if sa is not None:
            assert sa.payload == sb.payload
            assert sa.intensity == sb.intensity


def test_unbounded_config_refused():
    with pytest.raises(PermissionError):
        DevelopmentalNursery(config=NurseryConfig(duration_steps=None))


def test_summary_and_snapshot(tmp_path):
    nursery = _nursery(tmp_path)
    for step in range(60):
        nursery.stimulus_provider(step)
    summary = nursery.summary()
    assert summary["enabled"] is True
    assert summary["authority"] is False
    assert summary["ecology_event_count"] >= 0
    snap = nursery.snapshot()
    assert set(snap) >= {"config", "state", "ecology", "memory",
                         "stream", "safety", "summary"}


def test_close_episode_records(tmp_path):
    nursery = _nursery(tmp_path)
    for step in range(40):
        nursery.stimulus_provider(step)
    episode = nursery.close_episode(40, {"note": "test"})
    assert episode.step_end == 40
    assert nursery.memory.episodes


def test_max_events_per_step_respected(tmp_path):
    nursery = _nursery(tmp_path, max_events_per_step=2)
    for step in range(120):
        events = nursery.generate_step(step)
        assert len(events) <= 2


def test_state_counters_advance(tmp_path):
    nursery = _nursery(tmp_path)
    assert isinstance(nursery.state, NurseryState)
    for step in range(30):
        nursery.generate_step(step)
    assert nursery.state.step == 29
