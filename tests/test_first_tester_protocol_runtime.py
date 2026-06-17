"""First tester protocol runtime: bounded, docs/reports, no network/Git/publish."""

from __future__ import annotations

import os

from _first_tester_helpers import run_protocol

from solaris_ai_nn.first_tester_protocol import FirstTesterProtocolRuntime


def test_bounded_runtime_refuses_unbounded(tmp_path):
    rt = FirstTesterProtocolRuntime(tester_state_dir=str(tmp_path / "p"),
                                    max_runtime_s=0)
    res = rt.run()
    assert res["refused"] is True


def test_docs_generated(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    for key in ("session_script", "acceptance_criteria", "stop_conditions",
                "task_sheet", "handoff_guide", "review_template"):
        assert os.path.isfile(rt.doc_paths[key]), key


def test_reports_generated(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    reports = os.path.join(rt.protocol_dir, "reports")
    assert os.path.isfile(os.path.join(reports,
                                       "FIRST_TESTER_PROTOCOL_REPORT.md"))
    assert os.path.isfile(os.path.join(reports,
                                       "FIRST_TESTER_PROTOCOL_REPORT.json"))


def test_no_network_git_shell_publish_session(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    snap = rt.safety.snapshot()
    assert snap["can_access_network"] is False
    assert snap["can_run_git"] is False
    assert snap["can_run_shell"] is False
    assert snap["can_publish"] is False
    assert snap["can_install_packages"] is False
    assert snap["can_run_tester_session"] is False
    st = rt.protocol_status()
    assert st["runs_session"] is False
    assert st["published"] is False
