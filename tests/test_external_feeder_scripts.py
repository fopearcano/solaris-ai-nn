"""External feeder scripts: dry-run/help, JSONL flags, no Solaris imports, no network."""

from __future__ import annotations

import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FEEDERS = os.path.join(_ROOT, "tools", "external_feeders")

_SCRIPTS = (
    "chronos_absence_feeder.py", "machine_body_feeder.py",
    "manual_environment_writer.py", "project_artifact_feeder.py",
    "operator_pulse_writer.py", "local_weather_manual_writer.py",
)


def _run(script, *args):
    return subprocess.run([sys.executable, os.path.join(_FEEDERS, script), *args],
                          capture_output=True, text=True, cwd=_ROOT, timeout=60)


def test_scripts_have_help():
    for script in _SCRIPTS:
        proc = _run(script, "--help")
        assert proc.returncode == 0, script
        assert "--out" in proc.stdout and "--dry-run" in proc.stdout, script


def test_scripts_dry_run_emit_jsonl():
    for script in _SCRIPTS:
        proc = _run(script, "--out", "/tmp/_feed_unused.jsonl", "--dry-run")
        assert proc.returncode == 0, f"{script}: {proc.stderr}"
        first = [l for l in proc.stdout.splitlines() if l.strip()][0]
        json.loads(first)  # valid JSON


def test_scripts_write_jsonl(tmp_path):
    out = tmp_path / "events.jsonl"
    proc = _run("chronos_absence_feeder.py", "--out", str(out),
                "--absence-reason", "test")
    assert proc.returncode == 0
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert rows


def test_events_mark_read_only_true():
    for script in _SCRIPTS:
        proc = _run(script, "--out", "/tmp/_x.jsonl", "--dry-run")
        ev = json.loads([l for l in proc.stdout.splitlines() if l.strip()][0])
        assert ev["read_only"] is True, script


def test_events_mark_is_command_false():
    for script in _SCRIPTS:
        proc = _run(script, "--out", "/tmp/_x.jsonl", "--dry-run")
        ev = json.loads([l for l in proc.stdout.splitlines() if l.strip()][0])
        assert ev["is_command"] is False, script
        assert ev["debug_gloss_is_ground_truth"] is False, script
        assert ev["human_label_is_ground_truth"] is False, script


def test_scripts_do_not_import_solaris_runtime():
    for script in _SCRIPTS:
        text = open(os.path.join(_FEEDERS, script)).read()
        assert "import solaris_ai_nn" not in text, script
        assert "from solaris_ai_nn" not in text, script


def test_scripts_do_not_require_network():
    for script in _SCRIPTS:
        text = open(os.path.join(_FEEDERS, script)).read()
        for banned in ("import requests", "import socket", "urllib.request",
                       "http.client", "subprocess"):
            assert banned not in text, f"{script} uses {banned}"
