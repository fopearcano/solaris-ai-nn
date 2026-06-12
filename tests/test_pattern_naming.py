"""Tests for the internal pattern namer."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.pattern_naming import (
    FORBIDDEN_NAME_FRAGMENTS,
    TYPE_PREFIXES,
    InternalPatternNamer,
)
from solaris_ai_nn.protolanguage.symbols import (
    TOKEN_PATTERN,
    SymbolType,
)


def test_deterministic_tokens():
    a = InternalPatternNamer()
    b = InternalPatternNamer()
    sequence_a = [a.make_token(SymbolType.ABSENCE, "silence"),
                  a.make_token(SymbolType.HABIT, "rest loop"),
                  a.make_token(SymbolType.ABSENCE, "silence")]
    sequence_b = [b.make_token(SymbolType.ABSENCE, "silence"),
                  b.make_token(SymbolType.HABIT, "rest loop"),
                  b.make_token(SymbolType.ABSENCE, "silence")]
    assert sequence_a == sequence_b  # same inputs, same names
    assert sequence_a[0] == "ABS_SILENCE_0001"
    assert sequence_a[1] == "HAB_REST_0001"
    assert sequence_a[2] == "ABS_SILENCE_0002"  # counter advances
    for token in sequence_a:
        assert TOKEN_PATTERN.match(token)


def test_no_anthropomorphic_names():
    namer = InternalPatternNamer()
    token = namer.make_token(SymbolType.NEED, "soul searching")
    assert "SOUL" not in token  # forbidden qualifier dropped
    token2 = namer.make_token(SymbolType.UNKNOWN, "feel the unknown")
    assert "FEEL" not in token2
    assert len(FORBIDDEN_NAME_FRAGMENTS) >= 8
    # Debug labels are clearly secondary.
    label = namer.make_debug_label(SymbolType.HABIT, "rest loop")
    assert label.startswith("[debug label]")
    assert "internal sign" in label


def test_token_parse_works():
    namer = InternalPatternNamer()
    token = namer.make_token(SymbolType.EXECUTIVE_DECISION,
                             "inhibition")
    parsed = InternalPatternNamer.parse_token(token)
    assert parsed is not None
    assert parsed["prefix"] == "EXEC"
    assert parsed["symbol_type"] == SymbolType.EXECUTIVE_DECISION
    assert parsed["qualifier"] == "INHIBITI"
    assert parsed["counter"] == 1
    assert InternalPatternNamer.parse_token("not a token") is None
    assert InternalPatternNamer.parse_token("ZZZ_0001") is None
    # Every type has a prefix; prefixes are unique.
    assert len(TYPE_PREFIXES) == len(SymbolType.ALL)
    assert len(set(TYPE_PREFIXES.values())) == len(TYPE_PREFIXES)
