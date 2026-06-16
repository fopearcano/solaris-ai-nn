"""Replication consumes soak dossier/autopsy; missing artifact inconclusive."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import DevelopmentalReplicationRuntime
from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime


def _real_soak(state_dir):
    soak = DevelopmentalSoakRuntime(state_dir=state_dir,
                                    stage="developmental_soak_30d", max_ticks=6,
                                    max_runtime_s=20.0)
    soak.run_stage("developmental_soak_30d")
    soak.run_post_run_autopsy()
    soak.write_artifacts()
    return soak


def test_consumes_soak_dossier_and_autopsy(tmp_path):
    soak_dir = str(tmp_path / "soak")
    _real_soak(soak_dir)
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path / "rep"))
    run = rt.discover_run("soak_run", soak_dir, lineage_id="L1")
    # The soak report (dossier + autopsy live in SOAK_PROTOCOL_REPORT.json) is
    # discovered and indexed.
    assert run.soak_report_path
    assert rt.registry.artifact_index["soak_run"].discovered


def test_missing_soak_artifact_inconclusive(tmp_path):
    rt = DevelopmentalReplicationRuntime(state_dir=str(tmp_path / "rep"))
    run = rt.discover_run("no_soak", str(tmp_path / "empty"), lineage_id="L1")
    # No soak artifacts -> recorded as missing (uncertainty), never invented.
    assert not run.soak_report_path
    assert rt.registry.artifact_index["no_soak"].missing


def test_does_not_duplicate_soak_logic():
    import inspect

    from solaris_ai_nn.developmental_replication import replication_runtime

    src = inspect.getsource(replication_runtime)
    assert "DevelopmentalSoakRuntime" not in src  # consumes artifacts, not logic
