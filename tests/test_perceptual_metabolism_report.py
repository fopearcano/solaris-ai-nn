"""PerceptualMetabolismReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import (
    PerceptualMetabolismReportBuilder,
    PerceptualMetabolismRuntime,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _runtime(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=rt)
    met.update(events_this_tick=10, tick=0)
    return met


def test_markdown_generated(tmp_path):
    out = PerceptualMetabolismReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Perceptual Metabolism Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = PerceptualMetabolismReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove(tmp_path):
    report = PerceptualMetabolismReportBuilder(_runtime(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "not feelings" in not_prove
    assert "not biological life" in not_prove
    assert "does not prove consciousness" in not_prove
    assert report["sections"]["limitations"]


def test_claim_guard_scans_report(tmp_path):
    report = PerceptualMetabolismReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
