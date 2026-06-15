"""Desire: operator exposes active desires; Inner MAP includes motivation field."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver


def _runtime(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=2)
    rt.run_bounded()
    return rt


def test_operator_exposes_active_desires(tmp_path):
    rt = _runtime(tmp_path)
    router = QueryRouter(components={"desire_formation": rt})
    classifier = OperatorInputClassifier()
    for question in ("what desires are active", "did solaris act",
                     "why did it choose no action", "were any desires blocked"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:desire_formation" in resp.evidence_refs


def test_operator_safe_answers():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    want = router.route_query(classifier.classify("what does solaris want"))
    assert "does not have human wanting" in want.text.lower()
    emo = router.route_query(classifier.classify("are these emotions"))
    assert "not feelings or emotions" in emo.text.lower()
    agency = router.route_query(classifier.classify("does this prove agency"))
    assert "do not prove agency" in agency.text.lower()


def test_inner_map_includes_motivation_field(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(desire_formation=rt).update()
    assert model.desire_formation is not None
    assert model.desire_formation["desire_formation_enabled"] is True
    assert "motivation_field" in model.desire_formation
    assert "desire_formation" in model.to_dict()
