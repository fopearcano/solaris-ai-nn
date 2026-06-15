"""Ontogenesis: operator exposes concept counts; Inner MAP includes state."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


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
    return ont


def test_operator_exposes_concept_counts(tmp_path):
    ont = _runtime(tmp_path)
    router = QueryRouter(components={"perceptual_ontogenesis": ont})
    classifier = OperatorInputClassifier()
    for question in ("what concepts has solaris formed",
                     "which concepts are stable", "which concepts decayed",
                     "what world is forming"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:perceptual_ontogenesis" in resp.evidence_refs


def test_operator_understanding_answer_is_safe():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    resp = router.route_query(classifier.classify("does this prove understanding"))
    low = resp.text.lower()
    assert "no." in low
    assert "do not prove understanding" in low


def test_operator_human_concepts_answer_is_safe():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    resp = router.route_query(classifier.classify("are these human concepts"))
    low = resp.text.lower()
    assert "sensorium-native" in low
    assert "never ground truth" in low


def test_inner_map_includes_ontogenesis_state(tmp_path):
    ont = _runtime(tmp_path)
    model = InnerMapObserver(perceptual_ontogenesis=ont).update()
    assert model.perceptual_ontogenesis is not None
    assert model.perceptual_ontogenesis["perceptual_ontogenesis_enabled"] is True
    assert "perceptual_ontogenesis" in model.to_dict()
