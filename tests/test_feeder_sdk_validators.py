"""Validators: valid passes; missing provenance fails; command/decode rejected."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import EnvelopeValidator, FeederSDKEnvelope


def _valid_dict():
    return FeederSDKEnvelope(
        feeder_id="rf", source_id="rf", source_kind="external_feature_drop",
        modality="radio_frequency", features={"power": 0.6},
        timestamp=1.0).to_dict()


def test_valid_event_passes():
    assert EnvelopeValidator().validate(_valid_dict()).valid


def test_missing_provenance_fails():
    rec = _valid_dict()
    rec["provenance"] = {}
    result = EnvelopeValidator().validate(rec)
    assert result.valid is False
    assert any("provenance" in i.field for i in result.errors)


def test_command_like_text_not_command():
    # A human-text envelope whose annotation looks like a command is still a
    # valid observation; the validator does not execute or reject it as a cmd.
    env = FeederSDKEnvelope(
        feeder_id="t", source_id="t", source_kind="manual_log",
        modality="human_textual", features={"length": 12.0},
        annotation="shutdown now",
        annotation_status="human_label_external")
    assert EnvelopeValidator().validate(env.to_dict()).valid


def test_executable_payload_rejected():
    rec = _valid_dict()
    rec["command"] = "rm -rf /"
    assert EnvelopeValidator().validate(rec).valid is False


def test_decoded_private_content_rejected():
    rec = _valid_dict()
    rec["features"] = {"power": 0.6, "decoded_message": "secret"}
    result = EnvelopeValidator().validate(rec)
    assert result.valid is False
    assert any("private" in i.reason.lower() for i in result.errors)


def test_benign_no_raw_private_content_flag_ok():
    # The privacy flag "no_raw_private_content" must NOT trip the decode check.
    rec = _valid_dict()
    rec["privacy_flags"] = ["no_raw_private_content"]
    assert EnvelopeValidator().validate(rec).valid
