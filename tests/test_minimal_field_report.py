"""MinimalFieldOrganismDemoReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismDemoReportBuilder,
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)


def _runner(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "d"),
        config=OrganismicDemoConfig(ticks=40, seed=7))
    runner.run()
    return runner


def test_markdown_report_generated(tmp_path):
    out = MinimalFieldOrganismDemoReportBuilder(_runner(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    text = open(out["markdown"]).read()
    assert "Minimal Field Organism Demo Report" in text


def test_json_report_generated(tmp_path):
    out = MinimalFieldOrganismDemoReportBuilder(_runner(tmp_path)).write()
    assert os.path.isfile(out["json"])
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove_included(tmp_path):
    report = MinimalFieldOrganismDemoReportBuilder(_runner(tmp_path)).build()
    sections = report["sections"]
    assert sections["limitations"]
    not_prove = " ".join(sections["what_this_demo_does_not_prove"]).lower()
    assert "does not prove consciousness" in not_prove
    assert "does not prove sentience" in not_prove
    assert "does not prove understanding" in not_prove


def test_negative_results_included(tmp_path):
    report = MinimalFieldOrganismDemoReportBuilder(_runner(tmp_path)).build()
    assert "negative_results" in report["sections"]


def test_claim_guard_scans_report(tmp_path):
    report = MinimalFieldOrganismDemoReportBuilder(_runner(tmp_path)).build()
    assert report["claim_guard_safe"] is True
