"""ActionReactionReportBuilder: MD+JSON; limitations; ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.action_reaction import (
    ActionReactionReportBuilder,
    ActionReactionRuntime,
)
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _runtime(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    des.update(tick=0)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=3)
    ar.run_bounded()
    return ar


def test_markdown_generated(tmp_path):
    out = ActionReactionReportBuilder(_runtime(tmp_path)).write()
    assert os.path.isfile(out["markdown"])
    assert "Action-Reaction Report" in open(out["markdown"]).read()


def test_json_generated(tmp_path):
    out = ActionReactionReportBuilder(_runtime(tmp_path)).write()
    data = json.load(open(out["json"]))
    assert "sections" in data


def test_limitations_and_does_not_prove(tmp_path):
    report = ActionReactionReportBuilder(_runtime(tmp_path)).build()
    not_prove = " ".join(
        report["sections"]["what_this_does_not_prove"]).lower()
    assert "no real-world actuation occurred" in not_prove
    assert "operational effect, not feeling" in not_prove
    assert "does not prove agency" in not_prove
    assert "does not prove free will" in not_prove
    assert report["sections"]["limitations"]


def test_claim_guard_scans_report(tmp_path):
    report = ActionReactionReportBuilder(_runtime(tmp_path)).build()
    assert report["claim_guard_safe"] is True
