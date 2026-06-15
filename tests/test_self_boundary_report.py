"""SelfBoundaryReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import (
    SelfBoundaryReportBuilder,
    SelfBoundaryRuntime,
)


def _runtime(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             feeder_monitor_snapshot={"feeders": [
                                 {"feeder_id": "rf_feed"}]}, max_ticks=3)
    sb.run_bounded()
    return sb


def test_markdown_generated(tmp_path):
    out = SelfBoundaryReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Self-Boundary Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = SelfBoundaryReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove(tmp_path):
    report = SelfBoundaryReportBuilder(_runtime(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "operational, not subjective selfhood" in not_prove
    assert "not a biological body" in not_prove
    assert "not personhood" in not_prove
    assert "does not prove consciousness" in not_prove
    assert report["sections"]["limitations"]


def test_claim_guard_scans_report(tmp_path):
    report = SelfBoundaryReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
