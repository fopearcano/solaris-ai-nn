"""Live birth <-> Plural Sensorium + Perceptual Metabolism integration."""

from __future__ import annotations

import importlib.util
import json
import os

from solaris_ai_nn.live_birth import (
    EnvironmentalMembraneActivation,
    LiveEventEnvelope,
    LiveReadOnlyBirthRuntime,
    LiveSensoryEvent,
    approved_governance,
    feeder_registry_template,
)


def _accepted():
    raw = {"event_id": "e1", "timestamp_utc": "t", "source_id": "chronos_absence",
           "modality": "chronos", "channel": "c", "read_only": True,
           "is_command": False, "human_label_is_ground_truth": False,
           "payload": {"v": 1},
           "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                       "is_noisy": False}}
    env = LiveEventEnvelope(raw=raw, source_file="f", line_number=1)
    env.event = LiveSensoryEvent.from_dict(raw)
    return env


def test_sensorium_handoff_if_available():
    result = EnvironmentalMembraneActivation().activate([_accepted()])
    available = importlib.util.find_spec(
        "solaris_ai_nn.plural_sensorium") is not None
    assert result.sensorium_available == available
    if available:
        assert result.sensorium_handoff is True
    else:
        # Fallback: a placeholder report path is still produced.
        assert "placeholder" in result.detail.lower()


def _run(tmp_path):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    good = {"event_id": "e1", "timestamp_utc": "t", "source_id": "chronos_absence",
            "modality": "chronos", "channel": "c", "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": {"v": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}
    with open(os.path.join(state, "inbox", "e.jsonl"), "w") as fh:
        fh.write(json.dumps(good) + "\n")
    rt.run()
    return rt


def test_metabolism_handoff_report_only_if_available(tmp_path):
    rt = _run(tmp_path)
    available = importlib.util.find_spec(
        "solaris_ai_nn.perceptual_metabolism") is not None
    if available:
        assert "report-only" in rt.metabolism_status
        # Report-only: never requests more data or controls feeders.
        assert "may not request more data" in rt.metabolism_status
    else:
        assert "unavailable" in rt.metabolism_status.lower()


def test_membrane_read_only(tmp_path):
    rt = _run(tmp_path)
    assert rt.membrane["controls_feeders"] is False
    assert rt.membrane["requests_more_data"] is False
