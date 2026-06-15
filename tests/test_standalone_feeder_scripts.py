"""Standalone feeder scripts: exist; run; valid envelopes; no net/shell/hw."""

from __future__ import annotations

import importlib.util
import json
import os

from solaris_ai_nn.feeder_sdk import EnvelopeValidator

_FEEDERS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "feeders_sdk")
_SCRIPTS = ("feeder_template", "manual_log_feeder", "folder_rhythm_feeder",
            "system_rhythm_feeder", "feature_file_feeder", "simulated_rf_feeder",
            "simulated_echo_feeder", "simulated_vibration_feeder",
            "simulated_magnetic_feeder", "simulated_thermal_feeder",
            "multimodal_feeder_demo")


def _load(name):
    path = os.path.join(_FEEDERS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scripts_exist():
    for name in _SCRIPTS:
        assert os.path.isfile(os.path.join(_FEEDERS, name + ".py"))
    assert os.path.isfile(os.path.join(_FEEDERS, "README.md"))


def test_template_runs(tmp_path):
    mod = _load("feeder_template")
    env = mod.build_envelope("machine_rhythm", {"value": 0.5},
                             feeder_id="t", source_id="t")
    assert EnvelopeValidator().validate(env).valid


def test_simulated_feeders_generate_valid_envelopes():
    for name, gen_modality in (("simulated_rf_feeder", "radio_frequency"),
                               ("simulated_echo_feeder", "ultrasound_echo"),
                               ("simulated_vibration_feeder", "vibration"),
                               ("simulated_magnetic_feeder", "magnetic"),
                               ("simulated_thermal_feeder", "thermal_gradient")):
        mod = _load(name)
        events = mod.generate(20, 7)
        assert events
        validator = EnvelopeValidator()
        assert all(validator.validate(e).valid for e in events)
        assert all(e["trust_level"] == "simulated_fixture" for e in events)
        assert all(e["provenance"].get("simulated_fixture") for e in events)


def test_no_network_shell_hardware_requirement():
    for name in _SCRIPTS:
        src = open(os.path.join(_FEEDERS, name + ".py")).read()
        assert "import socket" not in src
        assert "urllib" not in src
        assert "requests" not in src
        assert "subprocess" not in src
        assert "os.system" not in src
