"""ResearchLeaderboard: generated; full not auto-first; not a mind ranking."""

from __future__ import annotations

from solaris_ai_nn.research_lab import LEADERBOARD_DIMENSIONS, ResearchLeaderboard


def test_leaderboard_generated():
    lb = ResearchLeaderboard()
    lb.add("full", "variant", {"g": {"prediction_accuracy": 0.6,
                                     "structural_change_score": 0.4}})
    lb.add("baseline", "baseline", {"g": {"prediction_accuracy": 0.0}})
    d = lb.to_dict()
    assert d["entries"]
    assert set(LEADERBOARD_DIMENSIONS) <= set(
        d["entries"][0]["scores"].keys())


def test_full_system_not_automatically_first():
    lb = ResearchLeaderboard()
    # A baseline with high safety/efficiency can outrank a weak "full" entry.
    lb.add("full", "variant", {"g": {"prediction_accuracy": 0.0,
                                     "memory_growth": 0.9}})
    lb.add("strong_baseline", "baseline",
           {"g": {"prediction_accuracy": 0.9, "invariant_pass_rate": 1.0,
                  "memory_growth": 0.0}}, evidence_count=5)
    assert lb.best() == "strong_baseline"


def test_not_a_consciousness_leaderboard():
    lb = ResearchLeaderboard()
    assert lb.to_dict()["is_consciousness_leaderboard"] is False
    assert "not a consciousness" in lb.to_dict()["note"]


def test_entries_show_limitations_and_evidence():
    lb = ResearchLeaderboard()
    entry = lb.add("full", "variant", {"g": {"prediction_accuracy": 0.5}},
                   evidence_count=2)
    assert entry.limitations
    assert entry.evidence_count == 2
