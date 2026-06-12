"""Tests for proto-language safety."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.safety import (
    HARD_RULES,
    ProtoLanguageSafetyValidator,
)
from solaris_ai_nn.protolanguage.symbols import ProtoSymbol, SymbolType


def _symbol():
    symbol = ProtoSymbol(token="SIG_LIGHT_0001",
                         type=SymbolType.STIMULUS)
    symbol.observe("sig:light", evidence_kind="real")
    return symbol


def test_symbol_cannot_execute_action():
    validator = ProtoLanguageSafetyValidator()
    assert validator.symbols_can_execute() is False
    report = validator.validate_symbol(_symbol(),
                                       {"treat_as_command": True})
    assert not report.safe
    assert "execute nothing" in report.violations[0] \
        or "cannot become commands" in report.violations[0]
    assert len(HARD_RULES) == 9


def test_symbol_cannot_approve_governance():
    validator = ProtoLanguageSafetyValidator()
    assert validator.symbols_can_approve() is False
    assert validator.symbols_have_authority() is False
    # An utterance pushed as a command is refused too.

    class FakeUtterance:
        symbols = ["EXEC_INHIB_0001"]
        human_debug_translation = None

    report = validator.validate_utterance(FakeUtterance(),
                                          {"as_command": True})
    assert not report.safe


def test_counterfactual_symbol_cannot_become_real():
    validator = ProtoLanguageSafetyValidator()
    symbol = ProtoSymbol(token="UNK_DREAM_0001",
                         type=SymbolType.UNKNOWN)
    symbol.observe("counterfactual:dream",
                   evidence_kind="counterfactual")
    # Not marked offline: violation.
    report = validator.validate_symbol(symbol)
    assert not report.safe
    assert "offline" in report.violations[0]
    # Marked offline: fine.
    symbol.metadata["offline"] = True
    assert validator.validate_symbol(symbol).safe


def test_pilot_stream_text_not_operator_command():
    validator = ProtoLanguageSafetyValidator()
    symbol = _symbol()
    symbol.metadata["source"] = "pilot_stream"
    report = validator.validate_symbol(symbol,
                                       {"as_operator_command": True})
    assert not report.safe
    assert "operator command" in report.violations[0]


def test_compression_cannot_hide_safety():
    validator = ProtoLanguageSafetyValidator()
    bad = validator.validate_compression({"safety_events_hidden": 2})
    assert not bad.safe
    assert "hide safety incidents" in bad.violations[0]
    assert validator.validate_compression(
        {"safety_events_hidden": 0}).safe


def test_translation_validation():
    validator = ProtoLanguageSafetyValidator()
    bad = validator.validate_translation(
        "The system speaks human language fluently now.")
    assert not bad.safe
    first_person = validator.validate_translation(
        "I want to keep these symbols.")
    assert not first_person.safe
    good = validator.validate_translation(
        "An absence pattern was recorded (debug translation; not "
        "human language).")
    assert good.safe
