"""Tests for the metric functions (deterministic, zero-safe)."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M


def test_continuity_metrics_from_mock_telemetry():
    tele = {"steps": 100, "heartbeats": 100, "checkpoints": 3, "restarts": 1,
            "brain_death_gap_seconds": 2.5, "unexpected_deaths": 0,
            "lifetime_steps": 200, "trace_event_count": 100}
    out = M.continuity_metrics(tele)
    assert out["heartbeat_count"] == 100
    assert out["heartbeat_jitter_estimate"] == 0.0
    assert out["restart_count"] == 1
    assert out["uptime_proxy_steps"] == 200
    assert out["trace_continuity_ratio"] == 1.0


def test_reactivity_metrics_from_mock_trace():
    tele = {"events": 50, "readout_updates": 25, "duration_seconds": 0.5}
    out = M.reactivity_metrics(tele, {"action_counts": {"a": 10, "b": 10},
                                      "mean_valence": 0.2})
    assert out["stimulus_count"] == 50
    assert out["reaction_count"] == 25
    assert out["avg_signal_to_suggestion_latency_s"] == 0.01
    assert out["response_diversity"] == 1.0  # perfectly even split
    assert out["average_reaction_valence"] == 0.2


def test_adaptation_metrics_handle_missing_data():
    out = M.adaptation_metrics(None)
    assert out["prediction_error_start"] == 0.0
    assert out["feedback_alignment_score"] is None
    improving = M.adaptation_metrics({"average_prediction_error": 1.0,
                                      "recent_prediction_error": 0.2,
                                      "readout_updates": 10})
    assert improving["prediction_error_trend"] == "improving"


def test_substrate_metrics_handle_zeros_safely():
    out = M.substrate_metrics_summary(None, state_size=0)
    assert out["state_norm"] == 0.0
    assert out["energy_proxy_active_units"] == 0.0
    out2 = M.substrate_metrics_summary({"activity_rate": 0.5}, state_size=64)
    assert out2["energy_proxy_active_units"] == 32.0


def test_habit_and_plasticity_metrics():
    habits = [{"weight": 0.9}, {"weight": -0.6}, {"weight": 0.1}]
    h = M.habit_metrics(habits, {"habit_reinforcements": 12})
    assert h["habit_pathway_count"] == 3
    assert h["strongest_habit_weight"] == 0.9
    assert 0.0 < h["habit_entropy"] <= 1.0
    p = M.plasticity_metrics({"applied_count": 3, "rejected_count": 1,
                              "rollback_count": 1})
    assert p["proposed_mutations"] == 4
    assert p["unsafe_proposal_rate"] == 0.25
    assert M.plasticity_metrics(None)["proposed_mutations"] == 0


def test_language_and_embodiment_metrics():
    lang = M.language_metrics({"meaning_atoms": 10},
                              {"a": {"text": "x", "grounded_in": ["f"]},
                               "b": {"text": "does not know y",
                                     "grounded_in": []}})
    assert lang["meaning_atom_count"] == 10
    assert lang["unknown_answer_count"] == 1
    assert lang["report_completeness_score"] == 0.5
    assert M.embodiment_metrics(None) == {"present": False}
