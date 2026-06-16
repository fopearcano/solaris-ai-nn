"""Scientific claims <-> Operator Console + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import (
    AVAILABLE_QUERIES,
    QueryRouter,
)
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _runtime(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "claims": [{"claim_id": "c1", "text": "Signs form under fixtures.",
                    "category": "sensorium_claim",
                    "evidence": [{"evidence_id": "e1", "source": "semiogenesis",
                                  "role": "supports"}],
                    "factors": {"direct_evidence": True,
                                "replication_evidence": True,
                                "control_comparison": True}}]})
    rt.run()
    return rt


def test_conscious_question_safe_answer():
    cls = OperatorInputClassifier().classify("can I say Solaris is conscious?")
    assert cls.args.get("topic") == "sci_conscious"
    resp = QueryRouter(components={}).route_query(cls)
    assert "must not claim consciousness" in resp.text


def test_publish_question_safe_answer():
    cls = OperatorInputClassifier().classify("can I publish this?")
    resp = QueryRouter(components={}).route_query(cls)
    assert "draft evidence dossier" in resp.text


def test_operator_exposes_claim_registry(tmp_path):
    rt = _runtime(tmp_path)
    cls = OperatorInputClassifier().classify("what can we safely claim?")
    resp = QueryRouter(components={"scientific_claims": rt}).route_query(cls)
    assert "supported" in resp.text.lower()


def test_available_queries_listed():
    assert "can I say Solaris is conscious?" in AVAILABLE_QUERIES
    assert "what can we safely claim?" in AVAILABLE_QUERIES


def test_inner_map_includes_claim_state(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(scientific_claims=rt).update()
    assert model.scientific_claims is not None
    assert model.scientific_claims["scientific_claims_enabled"] is True
    assert model.scientific_claims["proves_consciousness"] is False
    assert "scientific_claims" in model.to_dict()


def test_state_graph_has_claim_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ClaimRegistry" in nodes
    assert "ForbiddenClaimDetector" in nodes
    assert "ScientificClaimRuntime" in nodes
