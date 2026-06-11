"""Tests for the LLM claim filter."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.llm_adapter.claim_filter import LLMClaimFilter


def test_forbidden_phrase_detected():
    claim_filter = LLMClaimFilter()
    assert claim_filter.post_scan("The substrate processed 10 signals.")
    assert not claim_filter.post_scan(
        "The system is conscious and feels happy about the run.")
    assert claim_filter.post_scan_failures == 1


def test_safe_rewrite_suggested():
    claim_filter = LLMClaimFilter()
    unsafe = "the system wanted to rest"
    rewritten = claim_filter.suggest_rewrite(unsafe)
    assert ClaimGuard().is_safe(rewritten)
    ok, text = claim_filter.enforce(unsafe)
    assert ok
    assert ClaimGuard().is_safe(text)
    assert claim_filter.rewrites_applied >= 1


def test_failure_blocks_output():
    claim_filter = LLMClaimFilter()

    class StubbornGuard:
        def is_safe(self, text):
            return False

        def rewrite(self, text):
            return text  # rewriting achieves nothing

    claim_filter.guard = StubbornGuard()
    ok, text = claim_filter.enforce("anything")
    assert not ok
    assert text == ""
    assert claim_filter.refusals == 1


def test_pre_scan_drops_unsafe_facts():
    claim_filter = LLMClaimFilter()
    facts = claim_filter.pre_scan_facts(
        ["steps=10", "the system is conscious"])
    assert facts == ["steps=10"]
    assert claim_filter.pre_scan_failures == 1
