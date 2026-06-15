"""LiveFieldReportBuilder: MD + JSON; limitations; ClaimGuard; disclaimers."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldReportBuilder,
    LiveFieldRuntime,
)


def _runtime(tmp_path):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf.jsonl")
    with open(rf, "w") as fh:
        for i in range(6):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=rf))
    rt = LiveFieldRuntime(state_dir=base, live_root=base, registry=reg)
    rt.run(live=False)
    return rt


def test_markdown_report_generated(tmp_path):
    out = LiveFieldReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Live Field Report" in open(out["markdown"]).read()


def test_json_report_generated(tmp_path):
    out = LiveFieldReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_disclaimers_included(tmp_path):
    report = LiveFieldReportBuilder(_runtime(tmp_path)).build()
    sections = report["sections"]
    assert sections["limitations"]
    disclaimers = " ".join(sections["disclaimers"]).lower()
    assert "no hardware was controlled" in disclaimers
    assert "no source was modified" in disclaimers
    assert "does not prove consciousness" in disclaimers


def test_claim_guard_scans_report(tmp_path):
    report = LiveFieldReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
