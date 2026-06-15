"""ReportIndexer: reports indexed; limitations detected; corruption reported."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import ReportIndexer


def test_reports_indexed(tmp_path):
    base = str(tmp_path / "research")
    os.makedirs(base)
    with open(os.path.join(base, "research_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "ok"}, fh)
    index = ReportIndexer([base]).index()
    assert index.to_dict()["report_count"] == 1
    assert index.records[0].report_type == "research_report"


def test_limitations_detected_if_present(tmp_path):
    base = str(tmp_path / "arch")
    os.makedirs(base)
    with open(os.path.join(base, "architecture_review.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "review", "limitations": ["evidence is partial"],
                   "claim_guard_safe": True}, fh)
    index = ReportIndexer([base]).index()
    rec = index.records[0]
    assert rec.limitations_present is True
    assert rec.claim_guard_scanned is True


def test_missing_or_corrupt_report_reported(tmp_path):
    base = str(tmp_path / "safety")
    os.makedirs(base)
    with open(os.path.join(base, "safety_invariant_report.json"), "w",
              encoding="utf-8") as fh:
        fh.write("{not valid json")
    index = ReportIndexer([base]).index()
    rec = index.records[0]
    assert rec.report_type == "safety_invariant_report"
    assert rec.corrupted is True


def test_summary_and_recommendation_extracted(tmp_path):
    base = str(tmp_path / "pp")
    os.makedirs(base)
    with open(os.path.join(base, "post_pilot_analysis.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "growth was modest",
                   "recommendation": "extend the soak"}, fh)
    index = ReportIndexer([base]).index()
    rec = index.records[0]
    assert rec.summary == "growth was modest"
    assert rec.recommendation == "extend the soak"
