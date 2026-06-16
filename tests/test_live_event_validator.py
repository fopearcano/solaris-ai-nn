"""Live event validator: valid accepted, invalid/secret/command/forbidden quarantined."""

from __future__ import annotations

from solaris_ai_nn.live_birth import (
    LiveEventEnvelope,
    LiveEventValidator,
    QuarantineReason,
)

_ALLOWED = ["chronos_absence", "machine_body", "operator_pulse"]


def _validator():
    return LiveEventValidator(allowed_sources=_ALLOWED,
                              registered_sources=_ALLOWED)


def _envelope(raw):
    return LiveEventEnvelope(raw=raw, source_file="f.jsonl", line_number=1)


def _good():
    return {"event_id": "e", "timestamp_utc": "2026-06-16T18:00:00Z",
            "source_id": "chronos_absence", "modality": "chronos",
            "channel": "time", "read_only": True, "is_command": False,
            "human_label_is_ground_truth": False, "payload": {"tick": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}


def test_valid_event_accepted():
    result = _validator().validate(_envelope(_good()))
    assert result.accepted is True


def test_invalid_non_dict_quarantined():
    result = _validator().validate(_envelope("not a dict"))
    assert result.accepted is False
    assert result.quarantine_reason == QuarantineReason.INVALID_JSON


def test_secret_quarantined():
    raw = _good()
    raw["safety"]["contains_secret"] = True
    result = _validator().validate(_envelope(raw))
    assert result.quarantine_reason == QuarantineReason.CONTAINS_SECRET


def test_command_quarantined():
    raw = _good()
    raw["is_command"] = True
    result = _validator().validate(_envelope(raw))
    assert result.quarantine_reason == QuarantineReason.IS_COMMAND_TRUE


def test_forbidden_source_quarantined():
    raw = _good()
    raw["source_id"] = "raw_microphone"
    result = _validator().validate(_envelope(raw))
    assert result.quarantine_reason == QuarantineReason.SOURCE_FORBIDDEN


def test_missing_required_field_quarantined():
    raw = _good()
    del raw["payload"]
    result = _validator().validate(_envelope(raw))
    assert result.quarantine_reason == QuarantineReason.MISSING_REQUIRED_FIELD


def test_human_label_ground_truth_quarantined():
    raw = _good()
    raw["human_label_is_ground_truth"] = True
    result = _validator().validate(_envelope(raw))
    assert result.quarantine_reason == \
        QuarantineReason.HUMAN_LABEL_GROUND_TRUTH_TRUE


def test_validator_does_not_mutate_original():
    raw = _good()
    snapshot = dict(raw)
    _validator().validate(_envelope(raw))
    assert raw == snapshot
