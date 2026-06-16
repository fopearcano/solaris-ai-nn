"""Replication reports: markdown/json/matrix/falsification, ClaimGuard-scanned."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.developmental_replication import DevelopmentalReplicationRuntime


def _runtime(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path), max_runs=4)
    common = dict(sensorium_profile="non_human", fixture_live_replay="fixture",
                  developmental_profile={"composite_growth": 0.6,
                                         "structural_growth_status":
                                             "real_structural_growth",
                                         "durable_prediction_improvement_score":
                                             0.7},
                  world_signature={"concept_family_distribution": {"rf": 3}},
                  source_diet={"rf": 10})
    rt.register_run("a", lineage_id="L1", seed=7, **common)
    rt.register_run("c", lineage_id="L2", seed=9, sensorium_profile="human_like",
                    fixture_live_replay="fixture", human_label_exposure=0.8,
                    developmental_profile={"composite_growth": 0.2,
                                           "structural_growth_status":
                                               "fixture_overfit"},
                    world_signature={"concept_family_distribution": {"txt": 5},
                                     "human_label_contamination_score": 0.8},
                    source_diet={"txt": 30})
    rt.analyze()
    return rt


def test_markdown_and_json_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    assert os.path.isfile(out["markdown"])
    assert os.path.isfile(out["json"])
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    assert "replication_matrix" in data["sections"]


def test_matrix_and_falsification_reports_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    assert os.path.isfile(out["matrix"])
    assert os.path.isfile(out["falsification"])


def test_limitations_and_disclaimers_included(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    proofs = " ".join(report["sections"]["what_this_does_not_prove"]).lower()
    assert "experimental provenance, not biological ancestry" in proofs
    assert "cross-run similarity does not prove consciousness" in proofs
    assert "falsification passing does not prove understanding" in proofs


def test_claim_guard_scans_reports(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    assert report["claim_guard_safe"] is True
