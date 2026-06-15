"""Semiogenesis: architecture proposals; operator exposes signs; Inner MAP."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.architecture_evolution import semiogenesis_revision_proposals
from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime


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
    return sem


def test_architecture_consumes_report(tmp_path):
    sem = _runtime(tmp_path)
    proposals = semiogenesis_revision_proposals(sem.semiogenesis_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_contamination():
    status = {"contaminated_sign_ratio": 0.8, "gloss_dependence_score": 0.6,
              "sign_explosion_warning_count": 0,
              "modality_native_sign_ratio": 0.5,
              "private_syntax_pattern_count": 3, "internal_sign_count": 5}
    proposals = semiogenesis_revision_proposals(status)
    assert any(p["target"] == "contamination_mitigation" for p in proposals)


def test_operator_exposes_signs(tmp_path):
    sem = _runtime(tmp_path)
    router = QueryRouter(components={"semiogenesis": sem})
    classifier = OperatorInputClassifier()
    for question in ("what signs has solaris formed",
                     "what is solaris private language",
                     "did human labels contaminate signs"):
        resp = router.route_query(classifier.classify(question))
        assert resp.text
        assert "component:semiogenesis" in resp.evidence_refs


def test_operator_safe_answers():
    router = QueryRouter(components={})
    classifier = OperatorInputClassifier()
    words = router.route_query(classifier.classify("are these words"))
    assert "not human words" in words.text.lower()
    translate = router.route_query(classifier.classify("can you translate"))
    assert "approximate" in translate.text.lower()
    understand = router.route_query(
        classifier.classify("does this prove language understanding"))
    assert "does not prove language understanding" in understand.text.lower()


def test_inner_map_includes_semiogenesis_state(tmp_path):
    sem = _runtime(tmp_path)
    model = InnerMapObserver(semiogenesis=sem).update()
    assert model.semiogenesis is not None
    assert model.semiogenesis["semiogenesis_enabled"] is True
    assert "semiogenesis" in model.to_dict()
