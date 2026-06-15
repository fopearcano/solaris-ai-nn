"""Action-reaction: operator exposes action/reaction; Inner MAP includes state."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver


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


def test_operator_exposes_action_reaction_state(tmp_path):
    ar = _runtime(tmp_path)
    router = QueryRouter(components={"action_reaction": ar})
    classifier = OperatorInputClassifier()
    for question in ("what did solaris do", "what happened after it acted",
                     "did the action help", "what habits formed",
                     "what actions were inhibited"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        if question != "what did solaris do":
            assert "component:action_reaction" in resp.evidence_refs


def test_operator_real_world_answer_is_safe():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    resp = router.route_query(classifier.classify("did it act in the real world"))
    low = resp.text.lower()
    assert "no." in low
    assert "internal/simulated/report-only" in low


def test_inner_map_includes_action_reaction_state(tmp_path):
    ar = _runtime(tmp_path)
    model = InnerMapObserver(action_reaction=ar).update()
    assert model.action_reaction is not None
    assert model.action_reaction["action_reaction_enabled"] is True
    assert "action_reaction" in model.to_dict()
