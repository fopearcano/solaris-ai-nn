"""Tests for the LLM audit log."""

from __future__ import annotations

import json

from solaris_ai_nn.llm_adapter.audit import LLMAuditLog, text_hash
from solaris_ai_nn.llm_adapter.base import LLMRequest, LLMResponse, LLMTaskType


def _pair():
    request = LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                         input_text="Status summary: steps=5.")
    response = LLMResponse(request_id=request.request_id,
                           output_text="In plain terms: steps=5.",
                           used_context_refs=["context:ops"],
                           raw_model_name="mock")
    return request, response


def test_audit_writes_jsonl(tmp_path):
    audit = LLMAuditLog(state_dir=tmp_path)
    request, response = _pair()
    audit.record(request=request, response=response,
                 grounding_passed=True, claim_guard_passed=True,
                 adapter_type="mock")
    path = tmp_path / "llm_audit.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["task_type"] == "paraphrase_response"
    assert rows[0]["adapter_type"] == "mock"
    assert rows[0]["grounding_passed"] is True
    assert rows[0]["evidence_refs"] == ["context:ops"]


def test_prompt_output_hashes_stored_not_content(tmp_path):
    audit = LLMAuditLog(state_dir=tmp_path)
    request, response = _pair()
    event = audit.record(request=request, response=response)
    assert event.input_hash == text_hash(request.input_text)
    assert event.output_hash == text_hash(response.output_text)
    raw = (tmp_path / "llm_audit.jsonl").read_text()
    assert "Status summary: steps=5." not in raw  # hashes only
    assert "In plain terms" not in raw


def test_debug_mode_stores_truncated_content(tmp_path):
    audit = LLMAuditLog(state_dir=tmp_path, debug_store_content=True)
    request, response = _pair()
    event = audit.record(request=request, response=response)
    assert event.metadata["debug_input"].startswith("Status summary")


def test_fallback_recorded(tmp_path):
    audit = LLMAuditLog(state_dir=tmp_path)
    request, response = _pair()
    audit.record(request=request, response=response,
                 grounding_passed=False, fallback_used=True,
                 safety_decision="fallback")
    audit.record(request=request, response=response,
                 claim_guard_passed=False, fallback_used=True)
    snapshot = audit.snapshot()
    assert snapshot["fallback_count"] == 2
    assert snapshot["grounding_failure_count"] == 1
    assert snapshot["claim_guard_failure_count"] == 1
