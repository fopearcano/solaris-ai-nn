"""Replication runtime: bounded, loads registry, no feeder/hardware/teaching."""

from __future__ import annotations

import inspect

from solaris_ai_nn.developmental_replication import DevelopmentalReplicationRuntime
from solaris_ai_nn.developmental_replication import replication_runtime


def _two_runs(rt):
    common = dict(sensorium_profile="non_human", fixture_live_replay="fixture",
                  developmental_profile={"composite_growth": 0.6,
                                         "structural_growth_status":
                                             "real_structural_growth",
                                         "durable_prediction_improvement_score":
                                             0.7},
                  world_signature={"concept_family_distribution": {"rf": 3}},
                  source_diet={"rf": 10})
    rt.register_run("a", lineage_id="L1", seed=7, **common)
    rt.register_run("b", lineage_id="L1", seed=9, **common)


def test_bounded_runtime(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path), max_runs=4,
                                         max_runtime_s=15.0)
    _two_runs(rt)
    out = rt.analyze()
    assert out["refused"] is False
    assert out["run_count"] == 2


def test_unbounded_refused(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path), max_runs=0,
                                         max_runtime_s=0)
    assert rt.analyze()["refused"] is True


def test_loads_registry_and_falsifies_bounded(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path), max_runs=4,
                                         max_falsification_tests=6)
    _two_runs(rt)
    rt.analyze()
    assert len(rt.falsifications) <= 6
    assert rt.matrix is not None


def test_status_disclaims_ancestry_and_life(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path))
    _two_runs(rt)
    rt.analyze()
    st = rt.replication_status()
    assert st["is_biological_ancestry"] is False
    assert st["is_consciousness_or_personhood"] is False


def test_no_feeder_hardware_source_teaching_in_source():
    src = inspect.getsource(replication_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
    assert "start feeder" not in src.lower()
    assert "teaching_loop" not in src.lower()
