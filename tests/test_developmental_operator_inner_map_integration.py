"""Developmental: operator exposes phase/epoch/growth; Inner MAP includes state."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver


def _runtime(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_metabolism": {"source_diet_diversity": 0.5},
                 "perceptual_ontogenesis": {"proto_concept_count": 8,
                                            "stable_concept_count": 4},
                 "sensorium_cognition": {"prediction_success_rate": 0.5}},
        max_ticks=5)
    dev.run_bounded()
    return dev


def test_operator_exposes_phase_epoch_growth(tmp_path):
    dev = _runtime(tmp_path)
    router = QueryRouter(components={"developmental_life": dev})
    classifier = OperatorInputClassifier()
    for question in ("what changed over time", "did it mature", "is it stuck",
                     "did it regress", "is this just log accumulation"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:developmental_life" in resp.evidence_refs


def test_operator_safe_answers():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    dev = router.route_query(classifier.classify("is solaris developing"))
    assert "does not prove life or consciousness" in dev.text.lower()
    life = router.route_query(
        classifier.classify("does this prove life or consciousness"))
    assert "no." in life.text.lower()
    assert "does not prove biological life" in life.text.lower()


def test_inner_map_includes_developmental_state(tmp_path):
    dev = _runtime(tmp_path)
    model = InnerMapObserver(developmental_life=dev).update()
    assert model.developmental_life is not None
    assert model.developmental_life["developmental_life_enabled"] is True
    assert "developmental_life" in model.to_dict()
