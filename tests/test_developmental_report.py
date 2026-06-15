"""DevelopmentalLifeReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.developmental_life import (
    DevelopmentalLifeReportBuilder,
    LongHorizonDevelopmentalRuntime,
)


def _runtime(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_metabolism": {"source_diet_diversity": 0.5},
                 "perceptual_ontogenesis": {"proto_concept_count": 8,
                                            "stable_concept_count": 4},
                 "sensorium_cognition": {"prediction_success_rate": 0.5}},
        max_ticks=5, epoch_tick_span=2)
    dev.run_bounded()
    return dev


def test_markdown_generated(tmp_path):
    out = DevelopmentalLifeReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Developmental Life Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = DevelopmentalLifeReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove(tmp_path):
    report = DevelopmentalLifeReportBuilder(_runtime(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "not biological life" in not_prove
    assert "not consciousness milestones" in not_prove
    assert "does not prove consciousness" in not_prove
    assert "does not prove life" in not_prove
    assert "does not prove agency or free will" in not_prove
    assert report["sections"]["limitations"]


def test_claim_guard_scans_report(tmp_path):
    report = DevelopmentalLifeReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
