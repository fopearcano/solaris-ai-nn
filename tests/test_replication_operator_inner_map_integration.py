"""Replication: operator exposes matrix; Inner MAP includes replication status."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.developmental_replication import DevelopmentalReplicationRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog


def _runtime(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path), max_runs=4)
    common = dict(sensorium_profile="non_human", fixture_live_replay="fixture",
                  developmental_profile={"composite_growth": 0.6,
                                         "structural_growth_status":
                                             "real_structural_growth",
                                         "durable_prediction_improvement_score":
                                             0.7},
                  world_signature={"concept_family_distribution": {"rf": 3}},
                  source_diet={"rf": 10})
    rt.register_run("a", lineage_id="L1", seed=7, **common)
    rt.register_run("b", lineage_id="L1", seed=9, **common)
    rt.analyze()
    return rt


def test_operator_catalog_exposes_replication():
    catalog = ProfileCatalog()
    entries = [e for e in catalog._entries.values()
               if e.source_package == "developmental_replication"]
    assert entries


def test_operator_query_answers_replication(tmp_path):
    rt = _runtime(tmp_path)
    router = QueryRouter(components={"developmental_replication": rt})
    clf = OperatorInputClassifier()
    for q, frag in (("did the result replicate?", "replicated"),
                    ("which claims were falsified?", "falsified"),
                    ("does replication prove consciousness?", "No.")):
        resp = router.route_query(clf.classify(q))
        assert frag.lower() in resp.text.lower()


def test_consciousness_query_safe_without_component():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    resp = router.route_query(clf.classify(
        "does replication prove consciousness?"))
    assert "does not prove consciousness" in resp.text.lower()


def test_inner_map_includes_replication(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(developmental_replication=rt).update()
    assert model.developmental_replication is not None
    assert model.developmental_replication[
        "developmental_replication_enabled"] is True
    assert model.developmental_replication["is_biological_ancestry"] is False
