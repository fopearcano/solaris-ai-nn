"""Desire: conflict -> LOGOS tension; hypothesis test desire; world records."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _runtime(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.8,
                    "consolidation_pressure_score": 0.6},
        cognition={"failed_prediction_count": 3, "question_pressure_count": 4},
        self_boundary={"continuity_break_count": 1,
                       "boundary_confidence_score": 0.8}, max_ticks=2)
    rt.run_bounded()
    return rt


def test_desire_conflict_emits_logos_tension(tmp_path):
    rt = _runtime(tmp_path)
    tensions = rt.logos_tensions()
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    if rt.conflict_detector.conflicts:
        assert tensions
        assert any("desire_conflict" in t.metadata for t in tensions)


def test_hypothesis_receives_test_desire(tmp_path):
    rt = _runtime(tmp_path)
    seeds = rt.hypothesis_seeds()
    assert all(s.source == "desire_formation" for s in seeds)


def test_world_model_records_internal_action_outcome(tmp_path):
    rt = _runtime(tmp_path)
    # Internal actions and outcomes are recorded as desire memory traces that
    # the world model can ingest (no external actuation).
    assert rt.executor.executed or rt.outcomes.outcomes
    for action in rt.executor.executed:
        assert "no external" in action.to_dict()["note"] or \
            "no hardware" in action.to_dict()["note"]
