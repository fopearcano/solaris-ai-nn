"""FeederBlueprintRegistry: registered; no hardware exec; example envelopes ok."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import EnvelopeValidator, FeederBlueprintRegistry


def test_blueprints_registered():
    reg = FeederBlueprintRegistry()
    assert len(reg.blueprints) >= 9
    assert reg.get("rf_spectrum_feeder") is not None
    assert reg.get("mmwave_echo_feeder") is not None


def test_no_blueprint_executes_hardware():
    reg = FeederBlueprintRegistry()
    assert reg.snapshot()["any_executes_hardware"] is False
    for b in reg.all():
        assert b.executes_hardware is False


def test_example_envelopes_valid():
    reg = FeederBlueprintRegistry()
    validator = EnvelopeValidator()
    for b in reg.all():
        assert validator.validate(b.example_envelope()).valid, b.blueprint_id


def test_rf_blueprint_forbids_decoding():
    rf = FeederBlueprintRegistry().get("rf_spectrum_feeder")
    joined = " ".join(rf.safety_constraints).lower()
    assert "never decode communications" in joined
    assert "decoded messages" in " ".join(
        rf.what_solaris_must_not_receive).lower()
