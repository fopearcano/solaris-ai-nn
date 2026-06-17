"""Environmental membrane runtime: bounded, reports, impressions, no control."""

from __future__ import annotations

import inspect
import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _setup(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    for fx in ("sample_validated_events.jsonl",
               "sample_contaminated_events.jsonl"):
        src = os.path.join(_FIXTURES, fx)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(state, "inbox", fx))
    return state


def test_bounded_runtime_runs(tmp_path):
    state = _setup(tmp_path)
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = EnvironmentalMembraneRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    state = _setup(tmp_path)
    EnvironmentalMembraneRuntime(state_dir=state, require_governance=True).run()
    reports = os.path.join(state, "membrane", "reports")
    assert os.path.isfile(os.path.join(reports,
                                       "ENVIRONMENTAL_MEMBRANE_REPORT.md"))


def test_impressions_generated(tmp_path):
    state = _setup(tmp_path)
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    assert rt.membrane_status()["membrane_impression_count"] >= 1
    impressions = os.path.join(state, "membrane", "impressions",
                               "SENSORY_IMPRESSIONS.jsonl")
    assert os.path.isfile(impressions)


def test_status_flags_no_control(tmp_path):
    state = _setup(tmp_path)
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    st = rt.membrane_status()
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False


def test_no_unsupported_claims_in_reports(tmp_path):
    state = _setup(tmp_path)
    EnvironmentalMembraneRuntime(state_dir=state, require_governance=True).run()
    md = open(os.path.join(state, "membrane", "reports",
                           "ENVIRONMENTAL_MEMBRANE_REPORT.md")).read().lower()
    assert "no consciousness/life/agency claim is made" in md


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.environmental_membrane.membrane_runtime as rt_mod

    src = inspect.getsource(rt_mod)
    assert "subprocess" not in src
    assert "urllib" not in src
    assert "os.system" not in src
