"""Scientific claim runtime: bounded, reads evidence, writes reports, no exec."""

from __future__ import annotations

import inspect

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _bundle():
    return {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3,
                        "failed_replication_count": 0},
        "live_field": {"present": True},
        "claims": [
            {"claim_id": "c1", "text": "Signs form under bounded fixtures.",
             "category": "sensorium_claim",
             "evidence": [{"evidence_id": "e1", "source": "semiogenesis",
                           "role": "supports"},
                          {"evidence_id": "e2",
                           "source": "replication_falsification",
                           "role": "supports"}],
             "factors": {"direct_evidence": True, "replication_evidence": True,
                         "control_comparison": True}}],
    }


def test_bounded_runs(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is True


def test_reads_evidence_and_status(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.scientific_claims_status()
    assert st["scientific_claim_count"] == 1
    assert st["supported_claim_count"] == 1
    assert st["evidence_mapping_count"] == 2


def test_writes_reports(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    out = rt.write_artifacts()
    assert out["markdown"].endswith("SCIENTIFIC_CLAIM_REPORT.md")
    assert rt.scientific_claims_status()[
        "latest_scientific_claim_report_path"] is not None


def test_no_git_github_release_execution_in_source():
    import solaris_ai_nn.scientific_claims.claim_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src


def test_status_flags_no_release_git_github(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.scientific_claims_status()
    assert st["creates_release"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False
    assert st["modifies_source"] is False
    assert st["proves_consciousness"] is False
