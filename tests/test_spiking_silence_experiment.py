"""Tests for the spiking silence experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.spiking_silence import run_spiking_silence


def test_bounded_silence_experiment_runs():
    start = time.perf_counter()
    result = run_spiking_silence(steps=90, seed=7)
    elapsed = time.perf_counter() - start
    assert elapsed < 60.0  # no infinite loop
    assert set(result.per_substrate) == {"liquid_state", "spiking_recurrent"}
    for data in result.per_substrate.values():
        assert {"before", "during_silence", "after",
                "silence_state_shift", "went_inert"} <= set(data)


def test_absence_stimuli_affect_substrate_state():
    result = run_spiking_silence(steps=120, seed=7)
    for name, data in result.per_substrate.items():
        # The state moved during the silence phase (absence stimuli drove it).
        assert data["silence_state_shift"] > 0.0, name
        assert data["during_silence"]["drift"] > 0.0, name


def test_substrates_do_not_go_inert():
    result = run_spiking_silence(steps=120, seed=7)
    for name, data in result.per_substrate.items():
        assert data["went_inert"] is False, name
        assert data["during_silence"]["activity_rate"] > 0.0, name


def test_report_saved_to_state_dir(tmp_path):
    run_spiking_silence(steps=60, seed=3, substrates=["spiking_recurrent"],
                        state_dir=str(tmp_path / "silence"))
    assert (tmp_path / "silence" / "spiking_silence.json").exists()


def test_deterministic_per_seed():
    a = run_spiking_silence(steps=90, seed=5, substrates=["liquid_state"])
    b = run_spiking_silence(steps=90, seed=5, substrates=["liquid_state"])
    assert (a.per_substrate["liquid_state"]["silence_state_shift"]
            == b.per_substrate["liquid_state"]["silence_state_shift"])
