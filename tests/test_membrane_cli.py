"""Membrane CLI: doctor/run/impressions/report/memory; strict nonzero on blocker."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.cli import main
from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _setup(tmp_path, governance=True):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    if governance:
        json.dump(approved_governance(), open(os.path.join(
            state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    for fx in ("sample_validated_events.jsonl",
               "sample_contaminated_events.jsonl"):
        shutil.copy(os.path.join(_FIXTURES, fx),
                    os.path.join(state, "inbox", fx))
    return state


def test_cli_membrane_doctor(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["membrane-doctor", "--state-dir", state])
    assert rc == 0
    assert "environmental membrane doctor" in capsys.readouterr().out


def test_cli_membrane_run(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["membrane-run", "--state-dir", state, "--max-events", "500",
               "--require-governance"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "environmental membrane run" in out


def test_cli_membrane_impressions(tmp_path, capsys):
    state = _setup(tmp_path)
    main(["membrane-run", "--state-dir", state, "--require-governance"])
    rc = main(["membrane-impressions", "--state-dir", state])
    assert rc == 0
    assert "sensory impression index" in capsys.readouterr().out


def test_cli_membrane_report(tmp_path, capsys):
    state = _setup(tmp_path)
    main(["membrane-run", "--state-dir", state, "--require-governance"])
    rc = main(["membrane-report", "--state-dir", state])
    assert rc == 0
    assert "environmental membrane report" in capsys.readouterr().out


def test_cli_membrane_memory(tmp_path, capsys):
    state = _setup(tmp_path)
    main(["membrane-run", "--state-dir", state, "--require-governance"])
    rc = main(["membrane-memory", "--state-dir", state])
    assert rc == 0
    assert "membrane memory" in capsys.readouterr().out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    # Unapproved governance + require_governance -> doctor blocked -> nonzero.
    state = _setup(tmp_path, governance=False)
    from solaris_ai_nn.live_birth import governance_template
    json.dump(governance_template(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    rc = main(["membrane-doctor", "--state-dir", state, "--strict",
               "--require-governance"])
    assert rc == 2
