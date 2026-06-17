"""RC runtime: bounded, reports/manifest/docs/bundle generated, no network/publish."""

from __future__ import annotations

import os

from _tester_rc_helpers import run_rc, seed_ready_state

from solaris_ai_nn.tester_release_candidate import TesterRCRuntime


def test_bounded_runtime_refuses_unbounded(tmp_path):
    rt = TesterRCRuntime(tester_state_dir=str(tmp_path / "rc"),
                         max_runtime_s=0)
    res = rt.run()
    assert res["refused"] is True


def test_reports_generated(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    reports = os.path.join(rt.rc_dir, "reports")
    assert os.path.isfile(os.path.join(reports, "TESTER_RC_REPORT.md"))
    assert os.path.isfile(os.path.join(reports, "TESTER_RC_REPORT.json"))
    assert os.path.isfile(os.path.join(
        reports, "TESTER_RC_READINESS_REPORT.md"))


def test_manifest_and_docs_generated(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    assert os.path.isfile(os.path.join(rt.rc_dir, "manifests",
                                       "TESTER_RC_MANIFEST.json"))
    for key in ("release_notes", "quickstart", "runbook", "known_issues",
                "feedback_guide"):
        assert os.path.isfile(rt.doc_paths[key])


def test_bundle_generated(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    assert os.path.isdir(rt.bundle.bundle_dir)


def test_no_network_git_shell_publish(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    snap = rt.safety.snapshot()
    assert snap["can_access_network"] is False
    assert snap["can_run_git"] is False
    assert snap["can_run_shell"] is False
    assert snap["can_publish"] is False
    assert snap["can_upload_package"] is False
    assert snap["can_create_releases"] is False
    st = rt.rc_status()
    assert st["published"] is False
    assert st["uploaded"] is False
