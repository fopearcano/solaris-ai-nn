"""Metabolism surfaces in Research protocols, Operator console, and Inner MAP."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _metabolism(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"), sensorium=rt)
    met.update(events_this_tick=16, tick=0)
    return met


def test_research_protocols_registered():
    for name in ("perceptual_metabolism", "sensory_overload",
                 "sensory_deprivation", "source_diet", "consolidation_pressure",
                 "perceptual_metabolism_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_operator_console_exposes_overload_deprivation_diet(tmp_path):
    met = _metabolism(tmp_path)
    router = QueryRouter(components={"perceptual_metabolism": met})
    classifier = OperatorInputClassifier()
    for question in ("is solaris overloaded",
                     "is solaris sensorily deprived",
                     "which source dominates its diet"):
        cls = classifier.classify(question)
        resp = router.route_query(cls)
        assert resp.text
        assert "component:perceptual_metabolism" in resp.evidence_refs


def test_operator_console_needs_are_not_feelings():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    cls = classifier.classify("are these needs feelings")
    resp = router.route_query(cls)
    low = resp.text.lower()
    assert "not feelings" in low or "are not feelings" in low
    assert "operational" in low


def test_inner_map_includes_metabolism_state(tmp_path):
    met = _metabolism(tmp_path)
    observer = InnerMapObserver(perceptual_metabolism=met)
    model = observer.update()
    assert model.perceptual_metabolism is not None
    assert model.perceptual_metabolism["perceptual_metabolism_enabled"] is True
    # The serialized model carries the metabolism block too.
    assert "perceptual_metabolism" in model.to_dict()
