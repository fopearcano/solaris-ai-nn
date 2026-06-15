"""Action-reaction: hypothesis seeds; memory stores traces; latent replay rec."""

from __future__ import annotations

import os

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _runtime(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    des.update(tick=0)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=3)
    ar.run_bounded()
    return ar


def test_hypothesis_receives_action_effect(tmp_path):
    ar = _runtime(tmp_path)
    seeds = ar.hypothesis_seeds()
    assert all(s.source == "action_reaction" for s in seeds)


def test_memory_stores_traces(tmp_path):
    ar = _runtime(tmp_path)
    assert os.path.isfile(tmp_path / "ar" / "actions.jsonl")
    assert os.path.isfile(tmp_path / "ar" / "reactions.jsonl")
    assert os.path.isfile(tmp_path / "ar" / "consequences.jsonl")
    assert os.path.isfile(tmp_path / "ar" / "action_reaction_index.json")


def test_latent_replay_recommendation_exists(tmp_path):
    ar = _runtime(tmp_path)
    recs = ar.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6
