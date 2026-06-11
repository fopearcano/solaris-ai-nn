"""Tests for the deterministic prompt contracts."""

from __future__ import annotations

import pytest

from solaris_ai_nn.llm_adapter.base import LLMRequest, LLMTaskType
from solaris_ai_nn.llm_adapter.prompt_contracts import (
    GLOBAL_RULES,
    build_prompt,
    contract_for,
)


def _request():
    return LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                      input_text="Status summary: steps=5.",
                      allowed_facts=["steps=5", "health=ok"])


def test_contracts_include_allowed_facts():
    prompt = build_prompt(_request())
    assert "ALLOWED FACTS" in prompt
    assert "- steps=5" in prompt
    assert "- health=ok" in prompt
    assert "the only usable content" in prompt


def test_contracts_include_forbidden_claims():
    prompt = build_prompt(_request())
    assert "FORBIDDEN CLAIMS" in prompt
    assert "- is conscious" in prompt
    assert "- i want" in prompt


def test_contracts_instruct_refusal_on_insufficient_context():
    prompt = build_prompt(_request())
    assert "INSUFFICIENT CONTEXT" in prompt
    assert "REFUSAL:" in prompt
    # The refusal instruction is a global rule too.
    assert any("INSUFFICIENT CONTEXT" in rule for rule in GLOBAL_RULES)


def test_global_rules_cover_the_negatives():
    joined = " ".join(GLOBAL_RULES).lower()
    for fragment in ("do not invent facts", "consciousness",
                     "commands", "approve", "committed",
                     "counterfactual", "first person"):
        assert fragment in joined, fragment


def test_every_task_type_has_a_contract():
    for task in LLMTaskType.ALL:
        contract = contract_for(task)
        prompt = contract.build(LLMRequest(task_type=task,
                                           input_text="x",
                                           allowed_facts=["x"]))
        assert "GLOBAL RULES" in prompt
        assert "GROUNDING REQUIREMENT" in prompt
        assert "MAX LENGTH" in prompt
    with pytest.raises(KeyError):
        contract_for("mind_reading")
