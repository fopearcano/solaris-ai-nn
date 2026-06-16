"""Live feeder registry: loads, unknown blocked, control blocks, safe template."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import (
    FeederStatus,
    LiveFeederRecord,
    LiveFeederRegistry,
    feeder_registry_template,
)


def test_registry_loads(tmp_path):
    os.makedirs(os.path.join(str(tmp_path), "feeders"), exist_ok=True)
    with open(os.path.join(str(tmp_path), "feeders", "FEEDER_REGISTRY.json"),
              "w") as fh:
        json.dump(feeder_registry_template(), fh)
    reg = LiveFeederRegistry.load(str(tmp_path))
    assert reg.present is True
    assert reg.index()["live_feeder_count"] == 6


def test_unknown_feeder_untrusted_or_blocked():
    rec = LiveFeederRecord(feeder_id="x", source_id="some_unknown_source")
    assert rec.status in (FeederStatus.UNTRUSTED, FeederStatus.BLOCKED)


def test_solaris_may_control_blocks():
    rec = LiveFeederRecord(feeder_id="x", source_id="machine_body",
                           solaris_may_control=True)
    assert rec.status == FeederStatus.BLOCKED
    assert rec.blocks_birth is True


def test_read_only_false_blocks():
    rec = LiveFeederRecord(feeder_id="x", source_id="machine_body",
                           read_only=False)
    assert rec.status == FeederStatus.BLOCKED
    assert rec.blocks_birth is True


def test_template_safe_defaults():
    template = feeder_registry_template()
    for f in template["feeders"]:
        assert f["read_only"] is True
        assert f["started_externally"] is True
        assert f["solaris_may_control"] is False
