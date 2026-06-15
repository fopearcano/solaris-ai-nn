"""Cognition: operator exposes predictions/questions; Inner MAP includes state."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


def _runtime(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, max_ticks=6)
    ont.run_bounded()
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=5)
    sem.run_bounded()
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=4)
    cog.run_bounded()
    return cog


def test_operator_exposes_predictions_and_questions(tmp_path):
    cog = _runtime(tmp_path)
    router = QueryRouter(components={"sensorium_cognition": cog})
    classifier = OperatorInputClassifier()
    for question in ("what did solaris predict", "what did solaris get wrong",
                     "what questions does solaris have"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:sensorium_cognition" in resp.evidence_refs


def test_operator_safe_answers():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    thinking = router.route_query(classifier.classify("what is solaris thinking"))
    assert "not represented as human verbal thought" in thinking.text.lower()
    human = router.route_query(
        classifier.classify("is this human language reasoning"))
    assert "not human-language reasoning" in human.text.lower()


def test_inner_map_includes_cognition_state(tmp_path):
    cog = _runtime(tmp_path)
    model = InnerMapObserver(sensorium_cognition=cog).update()
    assert model.sensorium_cognition is not None
    assert model.sensorium_cognition["sensorium_cognition_enabled"] is True
    assert "sensorium_cognition" in model.to_dict()
