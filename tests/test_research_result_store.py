"""ResearchResultStore: results appended; artifact index; missing reported."""

from __future__ import annotations

import os

from solaris_ai_nn.research_lab import ExperimentResult, ResearchResultStore


def test_results_appended(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    store.record_result(ExperimentResult(experiment_id="e", arm_label="full",
                                         arm_kind="variant"))
    assert store.snapshot()["result_count"] == 1
    assert os.path.exists(os.path.join(str(tmp_path), "results.jsonl"))


def test_artifact_index_written(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    p = os.path.join(str(tmp_path), "real.json")
    with open(p, "w") as fh:
        fh.write("{}")
    entry = store.index_artifact("RES_1", p)
    assert entry.exists is True and entry.checksum
    assert os.path.exists(os.path.join(str(tmp_path), "artifact_index.jsonl"))


def test_missing_artifact_reported(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    store.index_artifact("RES_1", os.path.join(str(tmp_path), "nope.json"))
    assert store.missing_artifacts()


def test_result_records_seed_and_toggles(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    r = store.record_result(ExperimentResult(
        experiment_id="e", arm_label="v", arm_kind="variant", seed=11,
        module_toggles={"enable_memory": True}))
    assert r.seed == 11 and r.module_toggles["enable_memory"] is True


def test_unsafe_results_listed(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    store.record_result(ExperimentResult(experiment_id="e", arm_label="x",
                                         arm_kind="variant", safe=False,
                                         unsafe_reason="leak"))
    assert store.snapshot()["unsafe_results"]
