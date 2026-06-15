"""Self-boundary: operator exposes boundary state; Inner MAP includes it."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


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
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             max_ticks=3)
    sb.run_bounded()
    return sb


def test_operator_exposes_boundary_state(tmp_path):
    sb = _runtime(tmp_path)
    router = QueryRouter(components={"self_boundary": sb})
    classifier = OperatorInputClassifier()
    for question in ("what is solaris self-boundary",
                     "what belongs to solaris and what belongs to the world",
                     "did it maintain continuity after restart"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:self_boundary" in resp.evidence_refs


def test_operator_safe_answers():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    body = router.route_query(classifier.classify("does solaris have a body"))
    assert "not a biological body" in body.text.lower()
    aware = router.route_query(
        classifier.classify("does this prove self-awareness"))
    assert "does not prove self-awareness" in aware.text.lower()


def test_inner_map_includes_boundary_state(tmp_path):
    sb = _runtime(tmp_path)
    model = InnerMapObserver(self_boundary=sb).update()
    assert model.self_boundary is not None
    assert model.self_boundary["self_boundary_enabled"] is True
    assert "self_boundary" in model.to_dict()
