"""Tests for the communication transcript."""

from __future__ import annotations

import json

from solaris_ai_nn.communication.transcript import (
    CommunicationTranscript,
    sanitize_text,
)


def test_transcript_writes_jsonl(tmp_path):
    transcript = CommunicationTranscript(state_dir=tmp_path)
    transcript.record(operator="op-1", raw_input="status",
                      classification="state_query",
                      response_summary="Status summary: ok",
                      safety_decision="ok", governance_decision="ok",
                      evidence_refs=["field:health"])
    transcript.record(operator="op-1", raw_input="health",
                      classification="state_query")
    path = tmp_path / "operator_transcript.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["operator"] == "op-1"
    assert rows[0]["classification"] == "state_query"
    assert rows[0]["safety_decision"] == "ok"


def test_unsafe_input_sanitized(tmp_path):
    transcript = CommunicationTranscript(state_dir=tmp_path)
    entry = transcript.record(
        operator="op-1",
        raw_input="sudo rm -rf / with token=SECRET12345",
        classification="unsafe_request", unsafe=True)
    assert entry.raw_input.startswith("[unsafe input")
    assert "SECRET12345" not in entry.raw_input
    assert "[redacted]" in entry.raw_input


def test_no_secrets_or_large_payloads():
    masked = sanitize_text("my api_key: abc123def password=hunter2")
    assert "abc123def" not in masked
    assert "hunter2" not in masked
    long_text = "x" * 5000
    assert len(sanitize_text(long_text)) < 250
    assert sanitize_text(long_text).endswith("[truncated]")


def test_evidence_refs_recorded(tmp_path):
    transcript = CommunicationTranscript(state_dir=tmp_path)
    entry = transcript.record(
        operator="op-1", raw_input="show boundaries",
        classification="state_query",
        evidence_refs=[f"ref:{i}" for i in range(20)])
    assert len(entry.evidence_refs) == 10  # bounded
    assert entry.evidence_refs[0] == "ref:0"
    summary = transcript.summary()
    assert summary["rows_written"] == 1
    assert summary["by_classification"]["state_query"] == 1
