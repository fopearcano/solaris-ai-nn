"""Research <-> modules: summaries included if available; analysis is read-only."""

from __future__ import annotations

from solaris_ai_nn.research_lab import (
    ResearchMetricsSuite,
    ResearchReportBuilder,
)


def test_module_summaries_included_if_available():
    # Proto/world/LOGOS/hypothesis metrics flow through the shared suite.
    suite = ResearchMetricsSuite()
    groups = suite.compute({"metrics": {
        "proto_symbol_count": 5, "node_count": 10, "tension_count": 2,
        "hypothesis_count": 3}})
    assert groups["proto_language"]["proto_symbol_count"] == 5
    assert groups["world_model"]["node_count"] == 10
    assert groups["logos"]["tension_count"] == 2
    assert groups["hypothesis"]["hypothesis_count"] == 3


def test_analysis_only_report_does_not_mutate_module_state(tmp_path):
    # Building a report from provided summaries must not require or mutate live
    # module state; it only reads the dicts it is given.
    proto_summary = {"proto_symbol_count": 5}
    before = dict(proto_summary)
    ResearchReportBuilder(base_dir=str(tmp_path)).build(
        metrics_snapshot={"proto_language": proto_summary})
    assert proto_summary == before  # unchanged


def test_report_includes_metrics_snapshot(tmp_path):
    report = ResearchReportBuilder(base_dir=str(tmp_path)).build(
        metrics_snapshot={"world_model": {"node_count": 7}})
    assert report.sections["metrics"]["world_model"]["node_count"] == 7
