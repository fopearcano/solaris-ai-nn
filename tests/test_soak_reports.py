"""Soak reports: protocol report, dossier, autopsy, limitations, ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime


def _run(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="developmental_soak_30d", max_ticks=6,
                                  max_runtime_s=20.0, run_control_arms=True)
    rt.run_stage("developmental_soak_30d")
    rt.run_post_run_autopsy()
    return rt


def test_protocol_report_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    assert os.path.isfile(out["markdown"])
    assert os.path.isfile(out["json"])
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    assert "active_soak_plan" in data["sections"]


def test_dossier_and_autopsy_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["subreports"]}
    assert "EVIDENCE_DOSSIER.md" in names
    assert "POST_RUN_AUTOPSY.md" in names
    assert any(n.startswith("DAILY_PACKET_DAY_") for n in names)


def test_limitations_included(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    sections = report["sections"]
    assert sections["limitations"]
    proofs = " ".join(sections["what_this_does_not_prove"]).lower()
    assert "long runtime does not imply life" in proofs
    assert "persistence does not imply consciousness" in proofs
    assert "no human teaching loop" in proofs


def test_claim_guard_scans_report(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True
