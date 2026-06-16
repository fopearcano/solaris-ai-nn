"""Review assimilation runtime: bounded, reports, no publish/contact/training."""

from __future__ import annotations

import inspect

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _bundle():
    return {
        "independent_review": {
            "response_ledger": {"objections": []},
            "review_readiness": {
                "review_readiness_status": "ready_for_internal_review"}},
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "Could this be fixture overfit?",
             "claim_refs": ["c1"]}],
        "reproduction_outcomes": [
            {"challenge_type": "fixture_demo_reproduction",
             "status": "reproduced", "claim_refs": ["c1"]}],
    }


def test_bounded_runs(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path),
                                             max_runtime_s=0)
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    out = rt.write_artifacts()
    assert out["markdown"].endswith("REVIEW_ASSIMILATION_REPORT.md")
    assert rt.review_assimilation_status()[
        "latest_review_assimilation_report_path"] is not None


def test_status_flags_no_train_publish_contact(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.review_assimilation_status()
    assert st["trains_model"] is False
    assert st["published"] is False
    assert st["contacted_reviewers"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False


def test_no_publish_contact_train_exec_in_source():
    import solaris_ai_nn.review_assimilation.assimilation_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src
    assert "urllib" not in src
