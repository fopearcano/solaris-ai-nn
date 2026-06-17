"""Membrane <- Live Birth: accepted events handed to membrane; cert references it."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
)
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _setup(tmp_path):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    shutil.copy(os.path.join(_FIXTURES, "sample_validated_events.jsonl"),
                os.path.join(state, "inbox", "events.jsonl"))
    return state, rt


def test_accepted_live_events_handed_to_membrane(tmp_path):
    state, birth = _setup(tmp_path)
    birth.run()
    accepted = birth.live_birth_status()["live_event_accepted_count"]
    membrane = EnvironmentalMembraneRuntime(state_dir=state,
                                            require_governance=True)
    membrane.run()
    # The membrane processes the same accepted events Live Birth validated.
    assert membrane.membrane_status()["membrane_event_input_count"] == accepted
    assert membrane.membrane_status()["membrane_impression_count"] >= 1


def test_birth_certificate_can_reference_membrane_status(tmp_path):
    state, birth = _setup(tmp_path)
    birth.run()
    EnvironmentalMembraneRuntime(state_dir=state, require_governance=True).run()
    ref = birth.environmental_membrane_status()
    assert ref["environmental_membrane_available"] is True
    assert ref["live_birth_bypasses_membrane"] is False


def test_downstream_bypass_warning_generated(tmp_path):
    state, birth = _setup(tmp_path)
    birth.run()  # no membrane run yet
    ref = birth.environmental_membrane_status()
    assert ref["environmental_membrane_available"] is False
    assert ref["downstream_bypass_warning"]
