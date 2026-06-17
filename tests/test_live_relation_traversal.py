"""Live relation traversal: bounded, max depth respected, no invented relations."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import LiveRelationTraversal


def _syntax(n=5, blocked_last=False):
    rels = []
    nodes = [chr(ord("a") + i) for i in range(n)]
    for i in range(n - 1):
        rels.append({"source_sign": nodes[i], "target_sign": nodes[i + 1],
                     "relation_type": "source_linked", "strength": "weak",
                     "blocked": False})
    if blocked_last:
        rels.append({"source_sign": nodes[-1], "target_sign": "(none)",
                     "relation_type": "blocked_relation", "strength": "uncertain",
                     "blocked": True})
    return {"relations": rels}


def test_bounded_traversal():
    result = LiveRelationTraversal(max_depth=3).traverse(_syntax()).to_dict()
    assert result["path_count"] >= 1


def test_max_depth_respected():
    result = LiveRelationTraversal(max_depth=2).traverse(_syntax(6)).to_dict()
    assert result["max_observed_depth"] <= 2


def test_weak_relation_stays_weak():
    graph = LiveRelationTraversal(max_depth=3).traverse(_syntax())
    assert all(p.strength in ("weak", "uncertain") for p in graph.paths)


def test_blocked_relation_not_traversed():
    result = LiveRelationTraversal(max_depth=4).traverse(
        _syntax(4, blocked_last=True)).to_dict()
    # No path should include the blocked "(none)" target.
    for p in result["paths"]:
        assert "(none)" not in p["nodes"]


def test_empty_syntax():
    result = LiveRelationTraversal().traverse({"relations": []}).to_dict()
    assert result["traversal_status"] == "empty"
