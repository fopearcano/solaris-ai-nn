"""FeederPackBuilder: manifest + README generated; no feeder started."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.feeder_sdk import FeederPackBuilder
from solaris_ai_nn.feeder_sdk import packager


def test_manifest_generated(tmp_path):
    out = FeederPackBuilder(state_dir=str(tmp_path)).write()
    assert os.path.isfile(out["json"])
    data = json.load(open(out["json"]))
    assert data["feeders"]
    assert data["supported_modalities"]


def test_readme_generated(tmp_path):
    out = FeederPackBuilder(state_dir=str(tmp_path)).write()
    assert os.path.isfile(out["readme"])
    text = open(out["readme"]).read()
    assert "Feeder Pack" in text
    assert "Solaris does not start" in text


def test_no_feeder_started():
    # The packager never imports subprocess / network and starts nothing.
    src = inspect.getsource(packager)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "urllib" not in src


def test_manifest_lists_what_solaris_can_read(tmp_path):
    manifest = FeederPackBuilder(state_dir=str(tmp_path)).build()
    assert "validated event-envelope" in manifest.what_solaris_can_read
    assert manifest.schema_coverage > 0.0
