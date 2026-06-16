"""Compiler reports: report, index, per-experiment docs, ClaimGuard-scanned."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime


def _runtime(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=[
        {"proposal_id": "p1", "target": "revise_metabolism_thresholds",
         "proposal": "raise overload threshold",
         "evidence_refs": ["replication:ok"]},
        {"proposal_id": "p2", "target": "promote falsified module",
         "proposal": "promote X", "blocks_promotion": True}])
    rt.compile()
    return rt


def test_report_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    assert os.path.isfile(out["markdown"])
    assert os.path.isfile(out["json"])
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    assert "proposals_compiled" in data["sections"]
    assert "what_this_does_not_do" in data["sections"]


def test_compiled_index_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    assert os.path.isfile(out["index"])
    with open(out["index"], encoding="utf-8") as fh:
        assert "Compiled Experiment Index" in fh.read()


def test_per_experiment_docs_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    names = {os.path.basename(p) for p in out["per_experiment"]}
    for expected in ("IMPLEMENTATION_PROMPT.md", "BRANCH_SPEC.md",
                     "TEST_MATRIX.md", "SAFETY_GATES.md",
                     "OPERATOR_REVIEW_PACKET.md", "ROLLBACK_PLAN.md",
                     "VALIDATION_PLAN.md"):
        assert expected in names


def test_claim_guard_scans_reports(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    assert report["claim_guard_safe"] is True
    proofs = " ".join(report["sections"]["what_this_does_not_do"]).lower()
    assert "no source code was changed" in proofs
    assert "no git branch was created" in proofs
    assert "no external coding agent was run" in proofs
