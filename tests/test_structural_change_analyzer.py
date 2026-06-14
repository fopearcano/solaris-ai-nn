"""Post-pilot structural change: evidence with refs, conservative confidence."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import (
    BaselineComparator,
    StructuralChangeAnalyzer,
    StructuralChangeCategory,
)


class _Arts:
    class _Idx:
        present = ["developmental_state", "proto_symbols", "symbol_memory",
                   "autobiographical_memory"]
    index = _Idx()


def _cmp(before, after):
    return BaselineComparator().compare_dicts("before", before, "after", after)


def test_detects_memory_reorganization():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.5})
    evidence = StructuralChangeAnalyzer().analyze(cmp, _Arts())
    cats = {e.category for e in evidence}
    assert StructuralChangeCategory.MEMORY_REORGANIZATION in cats


def test_detects_proto_symbol_stabilization():
    cmp = _cmp({"ambiguous_symbol_ratio": 0.6},
               {"ambiguous_symbol_ratio": 0.3})
    evidence = StructuralChangeAnalyzer().analyze(cmp, _Arts())
    cats = {e.category for e in evidence}
    assert StructuralChangeCategory.PROTO_SYMBOL_STABILIZATION in cats


def test_evidence_has_before_after_refs():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.4})
    evidence = StructuralChangeAnalyzer().analyze(cmp, _Arts())
    assert evidence
    for e in evidence:
        assert e.before_ref == "before" and e.after_ref == "after"
        assert e.alternative_explanation
        assert 0.0 <= e.confidence <= 1.0


def test_persistence_marks_stability():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.5})
    windows = [_cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.2})]
    evidence = StructuralChangeAnalyzer().analyze(cmp, _Arts(),
                                                  persistence_windows=windows)
    mem = [e for e in evidence
           if e.category == "memory_reorganization"][0]
    assert mem.stability in ("persistent", "transient", "unknown")


def test_summary_shape():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.4})
    analyzer = StructuralChangeAnalyzer()
    evidence = analyzer.analyze(cmp, _Arts())
    summary = analyzer.summarize(evidence)
    assert "evidence_count" in summary and "mean_confidence" in summary
