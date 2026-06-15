"""Feeder scripts: exist; write envelopes; no source mutation/network/shell."""

from __future__ import annotations

import importlib.util
import json
import os

_FEEDERS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "feeders")
_SCRIPTS = ("manual_log_feeder", "watched_folder_feeder",
            "system_rhythm_feeder", "feature_dropbox_feeder")


def _load(name):
    path = os.path.join(_FEEDERS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_feeder_scripts_exist():
    for name in _SCRIPTS:
        assert os.path.isfile(os.path.join(_FEEDERS, name + ".py"))
    assert os.path.isfile(os.path.join(_FEEDERS, "README.md"))


def test_scripts_write_event_envelopes(tmp_path):
    manual = _load("manual_log_feeder")
    env = manual.make_envelope("ambient hum increased")
    assert env["modality"] == "human_textual"
    assert env["read_only"] is True
    assert env["source_mutable_by_solaris"] is False
    assert env["provenance"]["source_id"]
    sysr = _load("system_rhythm_feeder")
    senv = sysr.make_envelope(str(tmp_path))
    assert senv["modality"] == "machine_rhythm"
    assert senv["read_only"] is True


def test_watched_folder_does_not_modify_sources(tmp_path):
    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "a.txt").write_text("hello")
    before = (watch / "a.txt").read_text()
    folder = _load("watched_folder_feeder")
    envelopes = folder.scan_folder(str(watch))
    assert envelopes
    # The watched file is untouched.
    assert (watch / "a.txt").read_text() == before


def test_scripts_do_not_call_network_or_shell():
    for name in _SCRIPTS:
        src = open(os.path.join(_FEEDERS, name + ".py")).read()
        assert "import socket" not in src
        assert "urllib" not in src
        assert "requests" not in src
        assert "subprocess" not in src
        assert "os.system" not in src
