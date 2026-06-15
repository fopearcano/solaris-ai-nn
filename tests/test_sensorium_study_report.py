"""SensoriumDifferentiationStudyReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumDifferentiationStudyReportBuilder,
    default_study_design,
)


def _runner(tmp_path):
    design = default_study_design()
    design.ticks = 40
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner


def test_markdown_generated(tmp_path):
    out = SensoriumDifferentiationStudyReportBuilder(_runner(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Sensorium Differentiation Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = SensoriumDifferentiationStudyReportBuilder(_runner(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove_included(tmp_path):
    report = SensoriumDifferentiationStudyReportBuilder(_runner(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "does not prove consciousness" in not_prove
    assert "does not reveal subjective experience" in not_prove
    assert "does not rank beings" in not_prove


def test_claim_guard_scans_report(tmp_path):
    report = SensoriumDifferentiationStudyReportBuilder(_runner(tmp_path)).build()
    assert report["claim_guard_safe"] is True
