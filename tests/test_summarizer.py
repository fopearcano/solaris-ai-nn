"""Tests for the StructuralSummarizer."""

from __future__ import annotations

from solaris_ai_nn.language.meaning_trace import MeaningTraceBuilder
from solaris_ai_nn.language.schemas import ExplanationContext
from solaris_ai_nn.language.summarizer import StructuralSummarizer
from solaris_ai_nn.signals import canonical as C

S = StructuralSummarizer()


def test_summarizes_signal_counts():
    b = MeaningTraceBuilder()
    for _ in range(3):
        b.append_atoms(b.from_signal(C.Stimulus(payload="x", intensity=0.5)))
    b.append_atoms(b.from_signal(C.Stimulus(payload="y", is_absence=True)))
    summary = S.summarize_trace(b.to_trace())
    assert summary["atom_count"] == len(b)
    assert summary["by_category"]["signal"] > 0
    assert summary["dominant_category"] == "signal"
    assert summary["absence_count"] >= 1


def test_summarizes_session_with_actions_and_habits():
    ctx = ExplanationContext(
        telemetry={"events": 10, "reservoir_updates": 10,
                   "readout_updates": 5, "recent_prediction_error": 0.3},
        bridge={"substrate_type": "esn", "substrate_state_norm": 4.0,
                "substrate_activity_rate": 0.9, "habit_pathways": 2},
        habits=[{"pattern": "p", "action": "a", "weight": 0.9},
                {"pattern": "q", "action": "b", "weight": -0.2}],
        plasticity={"applied_count": 2, "rejected_count": 1},
        pruning={"passes": 1, "removed": 7},
    )
    summary = S.summarize_session(ctx)
    assert summary["signals"]["events"] == 10
    assert summary["substrate"]["type"] == "esn"
    assert summary["strongest_habits"][0]["weight"] == 0.9
    assert summary["plasticity"]["applied"] == 2
    assert summary["pruning"]["removed"] == 7


def test_summarizes_inner_map():
    digest = S.summarize_inner_map({
        "neural": {"substrate_type": "esn", "reservoir_state_norm": 4.0},
        "plasticity": {"habit_pathways": 3, "pruning_count": 1},
        "continuity": {"lifetime_steps": 100, "restart_count": 2},
        "embodiment": {"body": True},
    })
    assert digest["substrate_type"] == "esn"
    assert digest["restart_count"] == 2
    assert digest["embodiment_present"] is True


def test_summarize_experiment_adds_limitations():
    report = S.summarize_experiment({"steps": 10}, title="T")
    assert report.title == "T"
    assert report.sections["steps"] == 10
    assert report.limitations  # mandatory honesty section
