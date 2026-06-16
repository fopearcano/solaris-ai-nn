"""Compiler: research protocols exist; operator exposes ready/blocked specs."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog


def _runtime():
    rt = ExperimentCompilerRuntime(state_dir=".solaris_ai_nn_experiments/opx",
                                   max_specs=10)
    rt.load_manifest(proposals=[
        {"proposal_id": "p1", "target": "revise_metabolism_thresholds",
         "proposal": "raise threshold", "evidence_refs": ["replication:ok"]},
        {"proposal_id": "p2", "target": "actuate robot", "safe": False}])
    rt.compile()
    return rt


def test_research_protocols_exist():
    for name in ("experiment_compiler_protocol",
                 "prompt_pack_generation_protocol",
                 "branch_spec_generation_protocol", "test_matrix_protocol",
                 "safety_gate_protocol", "operator_review_packet_protocol",
                 "validation_plan_protocol"):
        assert name in PROTOCOLS


def test_operator_catalog_exposes_compiler():
    entries = [e for e in ProfileCatalog()._entries.values()
               if e.source_package == "experiment_compiler"]
    assert entries


def test_operator_query_exposes_ready_and_blocked():
    rt = _runtime()
    router = QueryRouter(components={"experiment_compiler": rt})
    clf = OperatorInputClassifier()
    ready = router.route_query(clf.classify(
        "what implementation prompts are ready?"))
    assert "ready" in ready.text.lower()
    blocked = router.route_query(clf.classify("which experiments are blocked?"))
    assert "blocked" in blocked.text.lower()


def test_operator_safe_answers():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    branch = router.route_query(clf.classify("did Solaris create a branch?"))
    assert "no." in branch.text.lower()
    assert "did not create git branches" in branch.text.lower()
    rewrite = router.route_query(clf.classify("did Solaris rewrite itself?"))
    assert "documents only" in rewrite.text.lower()
    nxt = router.route_query(clf.classify("what should I give Claude Code next?"))
    assert "implementation_prompt.md" in nxt.text.lower()
