"""Live private syntax: relation graph, weak relations, blocked, no language."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    LiveSignCandidate,
    PrivateSyntaxBuilder,
)


def _cand(sid, sources, modalities, refs=(), contamination=None):
    c = LiveSignCandidate(sign_id=sid, private_token=f"sig_live_{sid}",
                          linked_concept_ids=[f"c_{sid}"],
                          feature_signature_refs=list(refs))
    c.source_distribution = dict(sources)
    c.modality_distribution = dict(modalities)
    c.contamination_findings = contamination or []
    return c


def test_relation_graph_generated():
    a = _cand("a", {"machine_body": 5}, {"scalar": 5})
    b = _cand("b", {"machine_body": 4}, {"scalar": 4})
    g = PrivateSyntaxBuilder().build([a, b]).to_dict()
    assert g["live_private_syntax_relation_count"] >= 1


def test_weak_relation_marked_weak():
    a = _cand("a", {"machine_body": 5}, {"scalar": 5})
    b = _cand("b", {"machine_body": 4}, {"scalar": 4})
    graph = PrivateSyntaxBuilder().build([a, b])
    assert all(r.strength in ("weak", "uncertain", "strong")
               for r in graph.relations)
    assert any(r.strength in ("weak", "uncertain") for r in graph.relations)


def test_contaminated_relation_blocked():
    a = _cand("a", {"machine_body": 5}, {"scalar": 5})
    bad = _cand("bad", {"operator_pulse": 5}, {"pulse": 5},
                contamination=["operator_pulse_dominance"])
    g = PrivateSyntaxBuilder().build([a, bad]).to_dict()
    assert g["blocked_relation_count"] >= 1


def test_no_language_claim():
    a = _cand("a", {"machine_body": 5}, {"scalar": 5})
    b = _cand("b", {"machine_body": 4}, {"scalar": 4})
    g = PrivateSyntaxBuilder().build([a, b]).to_dict()
    for rel in g["relations"]:
        assert rel["is_language_grammar"] is False
        assert rel["is_semantics"] is False
