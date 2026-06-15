"""Action-reaction: Sensorium Lab action metrics; Architecture consumes report."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.architecture_evolution import action_reaction_revision_proposals
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _setup(tmp_path):
    ps = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    p = os.path.join(str(tmp_path), "rf.jsonl")
    with open(p, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    ps.add_feeder(fixture_feeder("rf_feed", p, "alien_rf"))
    ps.run_bounded(max_polls=1)
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7}, max_ticks=1)
    des.update(tick=0)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=3)
    ar.run_bounded()
    return ps, ar


def test_sensorium_lab_includes_action_metrics(tmp_path):
    ps, ar = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", ps,
                                        action_reaction=ar)
    data = sig.to_dict()
    assert "action_kind_distribution" in data
    assert "reaction_valence_distribution" in data
    assert "consequence_trace_profile" in data
    assert "habit_profile" in data
    assert "inhibition_profile" in data
    assert "no_effect_action_profile" in data
    assert "learned_policy_profile" in data


def test_architecture_evolution_consumes_report(tmp_path):
    _, ar = _setup(tmp_path)
    proposals = action_reaction_revision_proposals(ar.action_reaction_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_blocked_actions():
    status = {"reaction_count": 5, "disruptive_reaction_ratio": 0.2,
              "no_effect_action_count": 0, "blocked_action_count": 1,
              "strengthened_habit_count": 0}
    proposals = action_reaction_revision_proposals(status)
    assert any(p["target"] == "safety_gate_reinforcement" for p in proposals)
