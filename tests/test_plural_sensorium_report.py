"""PluralSensoriumReportBuilder: JSON + Markdown; contamination; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.plural_sensorium.reports import PluralSensoriumReportBuilder


def _runtime(tmp_path):
    path = os.path.join(tmp_path, "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(6):
            fh.write(json.dumps({"modality": "alien_rf", "v": 0.5,
                                 "ts": float(i)}) + "\n")
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path) + "/s")
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    return rt


def test_json_report_generated(tmp_path):
    rt = _runtime(str(tmp_path))
    out = PluralSensoriumReportBuilder(rt).write()
    assert os.path.isfile(out["json"])
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_markdown_generated(tmp_path):
    rt = _runtime(str(tmp_path))
    out = PluralSensoriumReportBuilder(rt).write()
    assert os.path.isfile(out["markdown"])
    text = open(out["markdown"]).read()
    assert "Plural Sensorium Report" in text


def test_contamination_score_included(tmp_path):
    rt = _runtime(str(tmp_path))
    report = PluralSensoriumReportBuilder(rt).build()
    assert "human_label_contamination_score" in report.sections
    assert "modality_native_grounding_score" in report.sections


def test_claim_guard_scans_report(tmp_path):
    rt = _runtime(str(tmp_path))
    report = PluralSensoriumReportBuilder(rt).build()
    assert report.claim_guard_safe is True
