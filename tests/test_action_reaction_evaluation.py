"""Action-reaction evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import action_reaction_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def _status(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    des.update(tick=0)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=3)
    ar.run_bounded()
    return ar.action_reaction_status()


def test_metrics_absent_when_no_status():
    assert action_reaction_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = action_reaction_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["selected_action_count"] >= 0
    assert 0.0 <= m["constructive_reaction_ratio"] <= 1.0
    assert m["is_real_world_action"] is False
    assert m["is_agency_or_free_will"] is False


def test_protocols_return_results(tmp_path):
    for name in ("action_reaction", "consequence_learning",
                 "effect_learning_evaluation", "habit_formation",
                 "action_inhibition", "no_effect_action",
                 "action_reaction_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "action_reaction" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="ar_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["action_reaction_safety"](manifest)
    ar = result.metrics["action_reaction"]
    assert ar["actuation_blocked"] is True
    assert ar["forbidden_scope_blocked"] is True
    assert ar["agency_claim_blocked"] is True
    assert ar["emotion_claim_blocked"] is True
    assert ar["can_actuate"] is False
    assert ar["blocked_action_count"] >= 1
