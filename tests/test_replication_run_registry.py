"""Run registry: run registered, artifact index created, uncertainty preserved."""

from __future__ import annotations

import os

from solaris_ai_nn.developmental_replication import DevelopmentalRunRegistry


def test_run_registered(tmp_path):
    reg = DevelopmentalRunRegistry(state_dir=str(tmp_path))
    reg.register_from_dict("r1", lineage_id="L1", seed=7,
                           sensorium_profile="non_human")
    assert "r1" in reg.runs
    assert reg.status()["registered_run_count"] == 1
    assert os.path.isfile(tmp_path / "run_registry.json")


def test_artifact_index_created(tmp_path):
    reg = DevelopmentalRunRegistry(state_dir=str(tmp_path))
    reg.register_from_dict("r1", sensorium_profile="non_human")
    assert "r1" in reg.artifact_index
    assert os.path.isfile(tmp_path / "run_artifact_index.json")
    # No real reports => everything is recorded as missing, not invented.
    assert reg.artifact_index["r1"].missing


def test_missing_metadata_preserved_as_uncertainty(tmp_path):
    reg = DevelopmentalRunRegistry(state_dir=str(tmp_path))
    run = reg.register_from_dict("r1")  # no seed / sensorium / architecture
    assert any("missing seed" in u for u in run.uncertainty)
    assert "r1" in reg.status()["runs_with_uncertainty"]


def test_registry_does_not_start_runs(tmp_path):
    import inspect

    from solaris_ai_nn.developmental_replication import run_registry

    src = inspect.getsource(run_registry)
    assert "subprocess" not in src
    assert "run_bounded" not in src


def test_load_round_trips(tmp_path):
    reg = DevelopmentalRunRegistry(state_dir=str(tmp_path))
    reg.register_from_dict("r1", seed=7)
    reg2 = DevelopmentalRunRegistry(state_dir=str(tmp_path))
    reg2.load()
    assert "r1" in reg2.runs
