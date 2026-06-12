"""Tests for governance and ops over proto-language."""

from __future__ import annotations

import inspect

from solaris_ai_nn.governance import GovernancePolicy, PermissionScope
from solaris_ai_nn.ops.supervisor import OperationalSupervisor
from solaris_ai_nn.protolanguage.safety import (
    ProtoLanguageSafetyValidator,
)


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_proto_language_allowed_in_bounded_runs():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"proto_language": True}))
    assert decision.allowed
    assert policy.permissions.allows(
        PermissionScope.ENABLE_PROTO_LANGUAGE)
    assert policy.permissions.allows(
        PermissionScope.ENABLE_SYMBOL_EMERGENCE)


def test_symbols_as_commands_named_in_policy():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"proto_language": True}),
        context={"symbols_as_commands": True})
    assert not decision.allowed
    assert any(v.rule_id == "symbols_never_execute"
               for v in decision.violations)
    rules = {r["rule_id"] for r in GovernancePolicy().to_dict()["rules"]
             if r["category"] == "protolanguage"}
    assert {"proto_language_allowed_bounded", "translation_claim_guard",
            "symbols_never_execute", "symbols_not_operator_language",
            "symbols_no_action_authority",
            "compression_cannot_hide_safety"} <= rules


def test_symbol_explosion_warning():
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split('developmental.get("proto_language")')[1]
    block = block.split("LLM adapter monitoring")[0]
    assert "symbol explosion" in block
    assert "ambiguity is dominating" in block
    assert "no stable proto-symbols" in block
    # Evidence only: no stop authority in the block.
    assert "request_shutdown" not in block


def test_compression_hiding_safety_blocked():
    validator = ProtoLanguageSafetyValidator()
    report = validator.validate_compression(
        {"safety_events_hidden": 1})
    assert not report.safe
    # The supervisor sees ops status fields via the developmental
    # summary (proto_language sub-dict); spot-check the keys exist.
    from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer

    summary = ProtoLanguageLayer().summary()
    for key in ("enabled", "symbol_count", "stable_symbol_count",
                "ambiguous_symbol_count", "symbol_memory_size",
                "last_symbol_event", "proto_language_report_path"):
        assert key in summary, key
