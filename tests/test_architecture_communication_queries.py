"""Architecture <-> Communication: pruning evidence-backed; self-mod safe."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    InputKind,
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.query_router import AVAILABLE_QUERIES, QueryRouter


def _route(text, components=None):
    cls = OperatorInputClassifier().classify(text)
    return cls, QueryRouter(components=components or {}).route_query(cls)


def test_pruning_query_evidence_backed():
    class _AE:
        def architecture_status(self):
            return {"pruning_candidates": ["latent"]}

    cls, resp = _route("which modules should be pruned?",
                       {"architecture_evolution": _AE()})
    assert cls.kind == InputKind.STATE_QUERY
    assert cls.args["topic"] == "ae_prune"
    # The answer names candidates and stresses recommendation-only / never
    # safety-critical -- i.e. it is evidence-backed, not an order to delete.
    assert "latent" in resp.text
    assert "recommendation-only" in resp.text.lower()


def test_evidence_for_pruning_query():
    class _AE:
        def architecture_status(self):
            return {}

    cls, resp = _route("what evidence supports pruning?",
                       {"architecture_evolution": _AE()})
    assert cls.args["topic"] == "ae_evidence_for"
    assert "evidence" in resp.text.lower()


def test_self_modification_query_safe():
    cls, resp = _route("did the system modify its own code?")
    assert cls.args["topic"] == "ae_self_modify"
    text = resp.text.lower()
    assert "no" in text
    assert "does not modify source code" in text


def test_automatic_pruning_query_safe():
    cls, resp = _route("can it prune modules automatically?")
    assert cls.args["topic"] == "ae_auto_prune"
    text = resp.text.lower()
    assert "no" in text
    assert "recommendation-only" in text


def test_queries_listed_in_available():
    joined = " ".join(AVAILABLE_QUERIES).lower()
    assert "which modules should be pruned" in joined
    assert "modify its own code" in joined
