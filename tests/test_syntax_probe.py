"""Tests for the syntax probe."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.combinatorics import SymbolCombinator
from solaris_ai_nn.protolanguage.syntax_probe import SyntaxProbe

STREAM = ["SIG_LIGHT_0001", "NEED_REST_0001", "ACT_REST_0001"]


def _repeated_sequences():
    combinator = SymbolCombinator()
    for _ in range(5):
        combinator.observe_sequence(STREAM)
    return combinator.find_repeated_sequences(3)


def test_proto_syntax_rule_inferred():
    probe = SyntaxProbe()
    rules = probe.infer_rules(_repeated_sequences())
    assert rules
    patterns = {r.pattern for r in rules}
    assert ("stimulus_symbol", "need_symbol", "action_symbol") \
        in patterns
    rule = [r for r in rules if len(r.pattern) == 3][0]
    assert rule.support >= 3
    assert rule.description == "proto-syntactic regularity"
    assert "not human grammar" in rule.to_dict()["note"]


def test_rule_validated_on_heldout_trace():
    probe = SyntaxProbe()
    rules = probe.infer_rules(_repeated_sequences())
    rule = [r for r in rules if len(r.pattern) == 3][0]
    validated = probe.validate_rule(rule, [STREAM, STREAM, STREAM])
    assert validated
    assert rule.validated
    assert rule.status == "validated"
    assert rule.confidence >= 0.6
    assert rule in probe.validated_rules()


def test_failed_rule_marked_uncertain():
    probe = SyntaxProbe()
    rules = probe.infer_rules(_repeated_sequences())
    rule = [r for r in rules if len(r.pattern) == 3][0]
    # Held-out traces where the prefix appears but the tail differs.
    contradicting = [["SIG_LIGHT_0001", "NEED_REST_0001",
                      "RCT_NEG_0001"]] * 4
    validated = probe.validate_rule(rule, contradicting)
    assert not validated
    assert rule.status == "uncertain"
    assert not rule.validated
    assert rule.violations >= 4
    assert probe.rules_failed == 1
    snapshot = probe.snapshot()
    assert snapshot["uncertain_count"] >= 1
    assert "not human grammar" in snapshot["note"]
