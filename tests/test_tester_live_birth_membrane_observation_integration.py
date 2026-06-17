"""Tester live birth/membrane/observation: full pipeline over the sample inbox."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_live_helpers import approve_governance  # noqa: E402


def _full_run(tmp_path):
    live = str(tmp_path / "live")
    TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        profile="tester_live_init_only_v0").run()
    approve_governance(live)
    rt = TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        write_templates=False, copy_safe_samples_to_inbox=True,
        run_birth=True, run_membrane=True, run_integration=True,
        run_observation=True)
    rt.run()
    return rt


def test_live_birth_called_on_sample_inbox(tmp_path):
    rt = _full_run(tmp_path)
    assert rt.birth_status.get("live_birth_blocked") is False


def test_membrane_generates_impressions(tmp_path):
    rt = _full_run(tmp_path)
    assert rt.membrane_status.get("membrane_impression_count", 0) >= 1


def test_integration_audit_runs(tmp_path):
    rt = _full_run(tmp_path)
    assert rt.integration_status.get("membrane_integration_enabled") is True
    assert "pipeline_status" in rt.integration_status


def test_observation_consumes_impressions(tmp_path):
    rt = _full_run(tmp_path)
    assert rt.observation_status.get("live_observation_enabled") is True


def test_unsafe_event_quarantined_in_live_run(tmp_path):
    # The safe pack's weather event is optional (not in allowed_sources) so it
    # is governance-quarantined; confirm quarantine is visible, not hidden.
    rt = _full_run(tmp_path)
    assert rt.quarantine_summary.get("quarantined_count", 0) >= 1
