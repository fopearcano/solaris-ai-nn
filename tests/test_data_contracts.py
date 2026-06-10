"""Tests for the read-only stream data contracts."""

from __future__ import annotations

from solaris_ai_nn.pilot.data_contracts import (
    MAX_PAYLOAD_CHARS,
    normalize_event,
    validate_jsonl_event,
    validate_text_line,
)


def test_valid_jsonl_event_accepted():
    result = validate_jsonl_event({
        "timestamp": 1700000000, "source": "lab_mic", "modality": "audio",
        "payload": "soft hum", "intensity": 0.4, "valence": 0.1,
        "novelty": 0.2, "tags": ["sample"], "metadata": {"room": "A"}})
    assert result.valid, result.reasons
    event = result.normalized
    assert event["source"] == "lab_mic"
    assert event["modality"] == "audio"
    assert event["intensity"] == 0.4


def test_malformed_jsonl_event_rejected():
    assert not validate_jsonl_event(["not", "an", "object"]).valid
    assert not validate_jsonl_event({"payload": "x", "intensity": "loud"}).valid
    assert not validate_jsonl_event({"payload": "x", "tags": "notalist"}).valid


def test_text_line_normalized():
    result = validate_text_line("the room is quiet\n", source="diary.txt")
    assert result.valid
    event = result.normalized
    assert event["modality"] == "text"
    assert event["payload"] == "the room is quiet"
    assert event["source"] == "diary.txt"
    assert 0.0 <= event["novelty"] <= 1.0


def test_command_like_payload_rejected():
    for payload in ("sudo rm -rf /", "rm -rf ~/data", "curl http://x.test",
                    "bash -c 'echo hi'", "result $(cat /etc/passwd)",
                    "a && b", "run `whoami` now"):
        assert not validate_text_line(payload).valid, payload
        assert not validate_jsonl_event({"payload": payload}).valid, payload


def test_action_request_keys_rejected():
    for key in ("command", "exec", "shell", "action_request", "open_url",
                "write_path"):
        result = validate_jsonl_event({key: "anything", "payload": "ok"})
        assert not result.valid, key


def test_url_and_path_action_requests_rejected():
    for payload in ("open https://example.test/page",
                    "fetch http://example.test/data",
                    "https://example.test/just-a-url",
                    "delete /etc/hosts", "write to /tmp/x"):
        assert not validate_text_line(payload).valid, payload
    # A URL *mentioned* inside prose is data, not an action request.
    assert validate_text_line(
        "the article mentioned example.test as a source").valid


def test_oversized_payload_rejected():
    big = "x" * (MAX_PAYLOAD_CHARS + 1)
    assert not validate_text_line(big).valid
    assert not validate_jsonl_event({"payload": big}).valid
    assert validate_text_line("x" * 100).valid


def test_binary_data_rejected():
    assert not validate_text_line(b"\x00\x01\x02").valid
    assert not validate_jsonl_event({"payload": b"\xff\xfe"}).valid
    assert not validate_text_line("text with \x00 NUL").valid


def test_normalize_clamps_and_strips_unknown_keys():
    event = normalize_event({"payload": "ok", "intensity": 9.0,
                             "valence": -5, "novelty": 2,
                             "surprise_key": "dropped",
                             "tags": ["a"] * 50})
    assert event["intensity"] == 1.0
    assert event["valence"] == -1.0
    assert event["novelty"] == 1.0
    assert "surprise_key" not in event
    assert len(event["tags"]) == 16
