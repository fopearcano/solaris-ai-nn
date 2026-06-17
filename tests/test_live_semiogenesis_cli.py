"""Live semiogenesis CLI: commands work; strict returns nonzero on blocker."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.cli import main
from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime

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
    shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    if chain:
        PostBirthLiveObservationRuntime(state_dir=state).run()
        FirstLiveOntogenesisRuntime(state_dir=state,
                                    allow_limited_birth=True).run()
    return state


def test_cli_live_semiogenesis(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-semiogenesis", "--state-dir", state,
               "--allow-limited-birth"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "first live semiogenesis" in out
    assert "sign birth gate status" in out


def test_cli_live_signs(tmp_path, capsys):
    state = _setup(tmp_path)
    main(["live-semiogenesis", "--state-dir", state, "--allow-limited-birth"])
    rc = main(["live-signs", "--state-dir", state])
    out = capsys.readouterr().out
    assert rc == 0
    assert "live sign memory" in out


def test_cli_live_sign_candidates(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-sign-candidates", "--state-dir", state,
               "--allow-limited-birth"])
    assert rc == 0
    assert "sign candidates" in capsys.readouterr().out


def test_cli_live_sign_birth_gate(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-sign-birth-gate", "--state-dir", state,
               "--allow-limited-birth"])
    assert rc == 0
    assert "sign birth gate" in capsys.readouterr().out


def test_cli_live_private_syntax(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-private-syntax", "--state-dir", state,
               "--allow-limited-birth"])
    assert rc == 0
    assert "private syntax" in capsys.readouterr().out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    state = _setup(tmp_path, chain=False)
    rc = main(["live-semiogenesis", "--state-dir", state, "--strict",
               "--require-birth-certificate", "--require-observation-stability",
               "--require-live-concepts"])
    assert rc == 2
