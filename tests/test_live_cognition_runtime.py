"""Live cognition runtime: bounded, reports, memory, no control/action."""

from __future__ import annotations

import inspect
import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime
from solaris_ai_nn.live_cognition import FirstLiveCognitionRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _setup(tmp_path, chain=True):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# cert\n")
    if os.path.isfile(_ONTO_FIXTURE):
        shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    if chain:
        PostBirthLiveObservationRuntime(state_dir=state).run()
        FirstLiveOntogenesisRuntime(state_dir=state,
                                    allow_limited_birth=True).run()
        FirstLiveSemiogenesisRuntime(state_dir=state,
                                     allow_limited_birth=True).run()
    return state


def _rt(state):
    return FirstLiveCognitionRuntime(
        state_dir=state, profile="live_cognition_anticipation_limited_v0")


def test_bounded_runtime_runs(tmp_path):
    state = _setup(tmp_path)
    assert _rt(state).run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = FirstLiveCognitionRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_and_memory_generated(tmp_path):
    state = _setup(tmp_path)
    _rt(state).run()
    reports = os.path.join(state, "cognition", "reports")
    assert os.path.isfile(os.path.join(reports, "LIVE_COGNITION_REPORT.md"))
    traces = os.path.join(state, "cognition", "traces")
    assert os.path.isfile(os.path.join(traces, "LIVE_COGNITION_MEMORY.json"))


def test_status_flags_no_control_no_action(tmp_path):
    state = _setup(tmp_path)
    rt = _rt(state)
    rt.run()
    st = rt.cognition_status()
    assert st["enables_action"] is False
    assert st["enables_action_reaction"] is False
    assert st["enables_developmental_autonomy"] is False
    assert st["enables_self_boundary"] is False
    assert st["signs_are_language_understanding"] is False
    assert st["traces_prove_reasoning"] is False
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False


def test_traces_built_on_stable_signs(tmp_path):
    state = _setup(tmp_path)
    rt = _rt(state)
    rt.run()
    assert rt.cognition_status()["live_cognition_trace_count"] >= 1


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.live_cognition.cognition_runtime as rt_mod

    src = inspect.getsource(rt_mod)
    assert "subprocess" not in src
    assert "urllib" not in src
    assert "os.system" not in src
