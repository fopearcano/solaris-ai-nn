"""Live cognition CLI: commands work; strict returns nonzero on blocker."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.cli import main
from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")
_PROFILE = ["--profile", "live_cognition_anticipation_limited_v0"]


def _setup(tmp_path, chain=True):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# cert\n")
    shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    if chain:
        PostBirthLiveObservationRuntime(state_dir=state).run()
        FirstLiveOntogenesisRuntime(state_dir=state,
                                    allow_limited_birth=True).run()
        FirstLiveSemiogenesisRuntime(state_dir=state,
                                     allow_limited_birth=True).run()
    return state


def test_cli_live_cognition(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-cognition", "--state-dir", state] + _PROFILE)
    out = capsys.readouterr().out
    assert rc == 0
    assert "first live cognition" in out
    assert "readiness gate" in out


def test_cli_live_cognition_traces(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-cognition-traces", "--state-dir", state] + _PROFILE)
    assert rc == 0
    assert "cognition traces" in capsys.readouterr().out


def test_cli_live_anticipations(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-anticipations", "--state-dir", state] + _PROFILE)
    assert rc == 0
    assert "anticipations" in capsys.readouterr().out


def test_cli_live_predictions(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-predictions", "--state-dir", state] + _PROFILE)
    assert rc == 0
    assert "prediction assessment" in capsys.readouterr().out


def test_cli_live_cognition_gate(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-cognition-gate", "--state-dir", state] + _PROFILE)
    assert rc == 0
    assert "readiness gate" in capsys.readouterr().out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    state = _setup(tmp_path, chain=False)
    rc = main(["live-cognition", "--state-dir", state, "--strict",
               "--require-birth-certificate", "--require-observation-stability",
               "--require-live-signs"] + _PROFILE)
    assert rc == 2
