"""Tester feeder templates: loads, external, no control, unknown blocked, invalid."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import (
    TesterFeederTemplateBuilder,
    TesterFeederTemplateRecord,
)


def test_feeder_registry_template_loads():
    reg = TesterFeederTemplateBuilder().build()
    assert reg.feeders
    ids = reg.source_ids()
    for src in ("chronos_absence", "machine_body", "local_environment_manual",
                "project_artifact_field", "operator_pulse"):
        assert src in ids


def test_feeders_marked_external():
    reg = TesterFeederTemplateBuilder().build()
    assert all(f.started_externally for f in reg.feeders)
    assert all(f.read_only for f in reg.feeders)


def test_solaris_may_control_false():
    reg = TesterFeederTemplateBuilder().build()
    assert all(not f.solaris_may_control for f in reg.feeders)
    assert not reg.invalid_records
    # to_dict marks started_by_solaris false explicitly.
    for f in reg.feeders:
        assert f.to_dict()["started_by_solaris"] is False


def test_controllable_feeder_is_invalid():
    bad = TesterFeederTemplateRecord(
        feeder_id="bad", source_id="x", modality="m", channel="c",
        description="d", writes_to="w", solaris_may_control=True)
    assert bad.valid is False


def test_optional_weather_included():
    reg = TesterFeederTemplateBuilder().build(include_optional=True)
    assert "local_weather_readonly_external" in reg.source_ids()
    reg2 = TesterFeederTemplateBuilder().build(include_optional=False)
    assert "local_weather_readonly_external" not in reg2.source_ids()


def test_load_marks_started_by_solaris_invalid(tmp_path):
    import json
    import os
    os.makedirs(os.path.join(str(tmp_path), "feeders"), exist_ok=True)
    from solaris_ai_nn.live_birth.feeder_registry import REGISTRY_FILENAME
    data = {"feeders": [{"feeder_id": "f", "source_id": "x", "modality": "m",
                         "channel": "c", "description": "d", "writes_to": "w",
                         "read_only": True, "started_externally": True,
                         "started_by_solaris": True}]}
    with open(os.path.join(str(tmp_path), "feeders", REGISTRY_FILENAME),
              "w") as fh:
        json.dump(data, fh)
    reg = TesterFeederTemplateBuilder.load(str(tmp_path))
    assert reg.invalid_records
