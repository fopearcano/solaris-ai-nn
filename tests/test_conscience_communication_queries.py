"""Communication integration: the 8 conscience runtime queries."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    IntegrationHealthMonitor,
    RunContext,
    RunMode,
)


def _router(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(RunContext(
        mode=RunMode.NURSERY_SIMULATED, state_dir=str(tmp_path), max_steps=20,
        enabled_modules=["bridge", "ecology", "governance", "world_model"]))
    orch.initialize()
    for _ in range(10):
        orch.step()
    return QueryRouter(components={
        "conscience": orch, "integration_health": IntegrationHealthMonitor()})


def _ask(router, text):
    clf = OperatorInputClassifier()
    return router.route_query(clf.classify(text))


def test_what_profile_is_running(tmp_path):
    r = _ask(_router(tmp_path), "what profile is running?")
    assert "nursery_simulated" in r.text


def test_simulated_or_real_month(tmp_path):
    r = _ask(_router(tmp_path), "is this a simulated month or real month?")
    assert "NOT a real month" in r.text or "simulated-time" in r.text


def test_can_this_run_for_months(tmp_path):
    r = _ask(_router(tmp_path), "can this run for months now?")
    assert "governance approval" in r.text
    assert "not by default" in r.text.lower()


def test_which_modules_are_running(tmp_path):
    r = _ask(_router(tmp_path), "which modules are running?")
    assert "enabled=" in r.text


def test_current_spine_phase(tmp_path):
    r = _ask(_router(tmp_path), "what is the current spine phase?")
    assert "spine phase" in r.text


def test_is_integration_healthy(tmp_path):
    r = _ask(_router(tmp_path), "is integration healthy?")
    assert "integration health" in r.text


def test_is_any_module_sovereign(tmp_path):
    r = _ask(_router(tmp_path), "is any module sovereign?")
    assert "no module is sovereign" in r.text


def test_show_conscience(tmp_path):
    r = _ask(_router(tmp_path), "show conscience")
    assert r.kind == "status"
    assert "no real-world action authority" in r.text


def test_queries_have_evidence(tmp_path):
    r = _ask(_router(tmp_path), "what profile is running?")
    assert any("conscience" in ref for ref in r.evidence_refs)
