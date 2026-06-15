"""DesireFormationReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.desire_formation import (
    DesireFormationReportBuilder,
    DesireFormationRuntime,
)


def _runtime(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.6},
        cognition={"failed_prediction_count": 2, "question_pressure_count": 3},
        self_boundary={"continuity_break_count": 1,
                       "boundary_confidence_score": 0.7}, max_ticks=3)
    rt.run_bounded()
    return rt


def test_markdown_generated(tmp_path):
    out = DesireFormationReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Desire Formation Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = DesireFormationReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove(tmp_path):
    report = DesireFormationReportBuilder(_runtime(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "valence is operational priority, not feeling" in not_prove
    assert "does not prove emotion" in not_prove
    assert "does not prove will" in not_prove
    assert "does not prove agency" in not_prove
    assert report["sections"]["limitations"]


def test_claim_guard_scans_report(tmp_path):
    report = DesireFormationReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
