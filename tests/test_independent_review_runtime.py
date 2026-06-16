"""Independent review runtime: bounded, reports, no publish/upload/Git/exec."""

from __future__ import annotations

import inspect

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _bundle():
    return {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 1,
                               "supported_claim_count": 1, "claims": [
                {"claim_id": "c1", "text": "Signs form.",
                 "category": "sensorium_claim", "status": "supported",
                 "evidence_refs": ["e1"], "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}},
        "sanitizer_inputs": {"abstract": "Signs form. It is not conscious."},
    }


def test_bounded_runs(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    out = rt.write_artifacts()
    assert out["markdown"].endswith("INDEPENDENT_REVIEW_REPORT.md")
    assert rt.independent_review_status()[
        "latest_independent_review_report_path"] is not None


def test_status_flags_no_publish_git(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.independent_review_status()
    assert st["published"] is False
    assert st["uploaded"] is False
    assert st["contacted_reviewers"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False


def test_no_publish_upload_exec_in_source():
    import solaris_ai_nn.independent_review.review_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src
    assert "urllib" not in src
