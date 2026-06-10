"""Tests for the substrate comparison experiment."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.experiments.substrate_comparison import run_substrate_comparison


def test_bounded_comparison_runs():
    start = time.perf_counter()
    result = run_substrate_comparison(steps=90, seed=7)
    elapsed = time.perf_counter() - start
    assert elapsed < 60.0  # no infinite loop
    assert result.steps == 90
    assert set(result.rows) == {"esn", "liquid_state", "spiking_recurrent"}


def test_produces_comparison_table_and_metrics():
    result = run_substrate_comparison(steps=90, seed=7,
                                      substrates=["esn", "spiking_recurrent"])
    table = result.table()
    assert "esn" in table and "spiking_recurrent" in table
    assert "activity_rate" in table
    assert "energy_proxy" in table
    for row in result.rows.values():
        for key in ("activity_rate", "state_drift_mean", "early_accuracy",
                    "late_accuracy", "recent_prediction_error",
                    "habit_reinforcements", "pruned_pathways",
                    "memory_trace_length", "duration_seconds", "energy_proxy"):
            assert key in row


def test_rejects_unknown_substrate():
    with pytest.raises(ValueError):
        run_substrate_comparison(steps=10, substrates=["esn", "nope"])


def test_report_saved_to_state_dir(tmp_path):
    run_substrate_comparison(steps=60, seed=3, substrates=["esn"],
                             state_dir=str(tmp_path / "cmp"))
    assert (tmp_path / "cmp" / "substrate_comparison.json").exists()


def test_deterministic_per_seed():
    a = run_substrate_comparison(steps=60, seed=11, substrates=["liquid_state"])
    b = run_substrate_comparison(steps=60, seed=11, substrates=["liquid_state"])
    assert a.rows["liquid_state"]["late_accuracy"] == b.rows["liquid_state"]["late_accuracy"]
    assert a.rows["liquid_state"]["state_drift_mean"] == b.rows["liquid_state"]["state_drift_mean"]
