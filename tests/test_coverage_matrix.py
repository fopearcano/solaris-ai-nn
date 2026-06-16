"""Coverage matrix: created, gaps visible, no empty green dashboard."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import (
    SpecComplianceAudit,
    build_coverage_matrix,
)


def _spec_compliance(**kw):
    return SpecComplianceAudit().audit(**kw)


def test_coverage_matrix_created():
    sc = _spec_compliance(
        spec={"proposed_changes": ["src/x.py"],
              "tests_required": ["tests/test_x.py"]},
        changed_files=["src/x.py", "tests/test_x.py"],
        test_results={"passed": 5, "failed": 0})
    matrix = build_coverage_matrix(spec_compliance=sc).to_dict()
    assert matrix["row_count"] >= 2


def test_gaps_visible():
    sc = _spec_compliance(
        spec={"proposed_changes": ["src/x.py"],
              "docs_required": ["docs/MISSING.md"]},
        changed_files=["src/x.py"])
    matrix = build_coverage_matrix(spec_compliance=sc).to_dict()
    assert matrix["coverage_gap_count"] >= 1


def test_no_empty_green_dashboard():
    # No spec => a single unknown row, not an all-green board.
    matrix = build_coverage_matrix(spec_compliance={}).to_dict()
    assert matrix["empty_green_dashboard"] is False
    assert matrix["row_count"] >= 1
    assert matrix["coverage_gap_count"] >= 1


def test_safety_gap_is_blocker():
    sc = _spec_compliance(
        spec={"safety_gates": ["no_source_self_rewrite"]},
        changed_files=["src/x.py"],
        test_results={"by_category": {"safety": {"passed": False}}})
    matrix = build_coverage_matrix(spec_compliance=sc).to_dict()
    assert matrix["blocker_count"] >= 1
