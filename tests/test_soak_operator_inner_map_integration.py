"""Soak: operator exposes status; Inner MAP includes soak status."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog


def _soak(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="dry_run_2h", max_ticks=4,
                                  max_runtime_s=15.0)
    rt.run_stage("dry_run_2h")
    return rt


def test_operator_catalog_exposes_soak():
    catalog = ProfileCatalog()
    soak_entries = [e for e in catalog._entries.values()
                    if e.source_package == "developmental_soak"]
    assert soak_entries


def test_operator_query_answers_soak(tmp_path):
    rt = _soak(tmp_path)
    router = QueryRouter(components={"developmental_soak": rt})
    clf = OperatorInputClassifier()
    for q, frag in (("what stage is the soak in?", "stage"),
                    ("did safety hold?", "safety"),
                    ("does this prove consciousness or life?", "No.")):
        resp = router.route_query(clf.classify(q))
        assert frag.lower() in resp.text.lower()


def test_soak_life_query_safe_without_component():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    resp = router.route_query(clf.classify(
        "does this prove consciousness or life?"))
    assert "does not prove" in resp.text.lower()


def test_inner_map_includes_soak(tmp_path):
    rt = _soak(tmp_path)
    model = InnerMapObserver(developmental_soak=rt).update()
    assert model.developmental_soak is not None
    assert model.developmental_soak["developmental_soak_enabled"] is True
    assert model.developmental_soak["is_biological_life"] is False
