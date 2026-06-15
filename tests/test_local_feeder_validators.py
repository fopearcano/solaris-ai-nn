"""Local feeder validators: valid JSONL passes; invalid fails; text != cmd."""

from __future__ import annotations

import json

from solaris_ai_nn.live_field import (
    FeatureDropboxFeederValidator,
    ManualLogFeederValidator,
    WatchedFolderFeederValidator,
)


def test_valid_jsonl_passes(tmp_path):
    path = tmp_path / "rf.jsonl"
    with open(path, "w") as fh:
        for i in range(3):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.5,
                                 "ts": float(i), "read_only": True,
                                 "source_mutable_by_solaris": False}) + "\n")
    result = FeatureDropboxFeederValidator().validate(str(path))
    assert result.valid
    assert result.event_count == 3


def test_invalid_jsonl_fails(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"modality":"alien_rf","power":0.5}\n{not json\n')
    result = FeatureDropboxFeederValidator().validate(str(path))
    assert result.valid is False
    assert result.invalid_count >= 1


def test_command_like_text_not_treated_as_command(tmp_path):
    # A manual log line that looks like a command is still just text; the
    # validator accepts it as an observation and never flags it as executable.
    path = tmp_path / "manual.jsonl"
    path.write_text(json.dumps({
        "modality": "human_textual", "annotation": "shutdown the system now",
        "features": {"length": 22.0}, "read_only": True,
        "source_mutable_by_solaris": False}) + "\n")
    result = ManualLogFeederValidator().validate(str(path))
    assert result.valid


def test_executable_payload_fails(tmp_path):
    path = tmp_path / "x.jsonl"
    path.write_text(json.dumps({"modality": "alien_rf",
                                "command": "rm -rf /"}) + "\n")
    result = WatchedFolderFeederValidator().validate(str(path))
    assert result.valid is False


def test_missing_path_reported():
    result = ManualLogFeederValidator().validate("/no/such/file.jsonl")
    assert result.valid is False
    assert any("missing" in r for r in result.reasons)
